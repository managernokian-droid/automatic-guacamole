"""Phase 1 — Price analysis module with cascade filters, charts and Excel export."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import clear_cache, load_suppliers
from utils.filter_manager import (
    FILTER_WIDGET_KEYS,
    apply_filters,
    delete_filter_set,
    load_saved_filters,
    render_cascade_filters,
    save_filter_set,
)

st.set_page_config(
    page_title="Аналіз цін — Nokian",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Session state defaults ---
for key, default in [
    ("df_suppliers", None),
    ("filters_applied", False),
    ("current_filters", {}),
    ("language", "ua"),
    ("df_nokian", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _col(df: pd.DataFrame, *candidates) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _export_excel(df: pd.DataFrame) -> BytesIO:
    output = BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)
    return output


def _display_table(df: pd.DataFrame, page_key: str = "page") -> None:
    PAGE_SIZE = 50
    total = len(df)
    n_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

    if n_pages > 1:
        col_left, col_right = st.columns([3, 1])
        with col_right:
            page = st.number_input(
                f"Сторінка (з {n_pages})",
                min_value=1,
                max_value=n_pages,
                value=1,
                step=1,
                key=page_key,
            )
    else:
        page = 1

    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    df_show = df.iloc[start:end].copy()
    for col in df_show.select_dtypes(include="category").columns:
        df_show[col] = df_show[col].astype(str)
    st.dataframe(df_show, use_container_width=True, height=400)
    st.caption(f"Показано {min(end, total)} з {total:,} рядків")


def _build_charts(df: pd.DataFrame) -> None:
    wholesale_col = _col(df, "Исходная оптовая цена", "Вихідна оптова ціна")
    class_col = _col(df, "Класс", "Клас")
    supplier_col = _col(df, "Поставщик", "Постачальник")

    if wholesale_col is None:
        st.warning("Не знайдено колонку з оптовою ціною.")
        return

    df_plot = df.copy()
    df_plot[wholesale_col] = pd.to_numeric(df_plot[wholesale_col], errors="coerce")
    df_plot = df_plot.dropna(subset=[wholesale_col])

    col1, col2 = st.columns(2)

    # Histogram
    with col1:
        st.subheader("Розподіл оптових цін")
        fig_hist = px.histogram(
            df_plot,
            x=wholesale_col,
            nbins=40,
            labels={wholesale_col: "Оптова ціна, грн"},
            color_discrete_sequence=["#1f77b4"],
        )
        fig_hist.update_layout(
            xaxis_title="Оптова ціна, грн",
            yaxis_title="Кількість позицій",
            showlegend=False,
            margin=dict(l=0, r=0, t=30, b=0),
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    # Box plot by class
    with col2:
        if class_col:
            st.subheader("Ціни за класами")
            fig_box = px.box(
                df_plot,
                x=class_col,
                y=wholesale_col,
                color=class_col,
                labels={wholesale_col: "Оптова ціна, грн", class_col: "Клас"},
            )
            fig_box.update_layout(
                showlegend=False,
                margin=dict(l=0, r=0, t=30, b=0),
            )
            st.plotly_chart(fig_box, use_container_width=True)
        else:
            st.info("Колонка 'Клас' не знайдена.")

    # Bar chart top-20 suppliers
    if supplier_col:
        st.subheader("Топ-20 постачальників за кількістю позицій")
        top_suppliers = (
            df_plot[supplier_col]
            .value_counts()
            .head(20)
            .reset_index()
        )
        top_suppliers.columns = ["Постачальник", "Кількість"]
        fig_bar = px.bar(
            top_suppliers,
            x="Кількість",
            y="Постачальник",
            orientation="h",
            color="Кількість",
            color_continuous_scale="Blues",
            labels={"Кількість": "Кількість позицій"},
        )
        fig_bar.update_layout(
            yaxis={"categoryorder": "total ascending"},
            showlegend=False,
            margin=dict(l=0, r=0, t=30, b=0),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_bar, use_container_width=True)


def _table_columns(df: pd.DataFrame) -> list[str]:
    preferred = [
        "Поставщик", "Постачальник",
        "Полное название", "Повна назва",
        "Класс", "Клас",
        "Бренд",
        "Модель",
        "Сезон",
        "Год изготовления шин", "Рік виготовлення шин",
        "Исходная оптовая цена", "Вихідна оптова ціна",
        "Исходная розничная цена", "Вихідна роздрібна ціна",
    ]
    return [c for c in preferred if c in df.columns]


# ---------------------------------------------------------------------------
# Sidebar — data loading
# ---------------------------------------------------------------------------

st.sidebar.title("📊 Аналіз цін")
st.sidebar.header("Завантаження даних")

uploaded_suppliers = st.sidebar.file_uploader(
    "База постачальників (Excel)",
    type=["xlsx", "xls"],
    key="upload_suppliers",
)

force_reload = st.sidebar.button("🔄 Очистити кеш і перезавантажити")

if force_reload and st.session_state.df_suppliers is not None:
    clear_cache()
    st.session_state.df_suppliers = None
    st.session_state.filters_applied = False
    st.session_state.current_filters = {}
    st.rerun()

load_message = ""
if uploaded_suppliers is not None:
    if st.session_state.df_suppliers is None or force_reload:
        with st.spinner("Завантаження даних..."):
            df, msg = load_suppliers(uploaded_suppliers, force_reload=force_reload)
            st.session_state.df_suppliers = df
            load_message = msg

st.sidebar.divider()

# ---------------------------------------------------------------------------
# Sidebar — cascade filters (only if data loaded)
# ---------------------------------------------------------------------------

if st.session_state.df_suppliers is not None:
    df_full = st.session_state.df_suppliers
    st.sidebar.header("Фільтри")

    # Track filter changes to reset filters_applied
    prev_filters = st.session_state.current_filters.copy()

    new_filters = render_cascade_filters(df_full)

    # Check if class is selected (mandatory)
    class_selected = bool(new_filters.get("class"))

    # Detect any change in filters
    if new_filters != prev_filters:
        st.session_state.filters_applied = False
        st.session_state.current_filters = new_filters

    st.sidebar.divider()

    col_apply, col_reset = st.sidebar.columns(2)
    with col_apply:
        apply_btn = st.sidebar.button(
            "✅ Застосувати фільтри",
            disabled=not class_selected,
            use_container_width=True,
            key="btn_apply",
        )
    with col_reset:
        reset_btn = st.sidebar.button(
            "🔄 Скинути фільтри",
            use_container_width=True,
            key="btn_reset",
        )

    if not class_selected:
        st.sidebar.warning("⚠️ Оберіть хоча б один Клас для активації фільтрів.")

    if reset_btn:
        st.session_state.current_filters = {}
        st.session_state.filters_applied = False
        for k in FILTER_WIDGET_KEYS:
            st.session_state.pop(k, None)
        st.rerun()

    if apply_btn and class_selected:
        st.session_state.filters_applied = True

    # --- Saved filter sets ---
    st.sidebar.divider()
    st.sidebar.subheader("💾 Збережені фільтри")
    saved = load_saved_filters()

    filter_name = st.sidebar.text_input("Назва набору фільтрів", key="filter_name_input")
    save_col, _ = st.sidebar.columns([2, 1])
    with save_col:
        if st.sidebar.button("Зберегти фільтр", key="btn_save_filter"):
            if filter_name.strip():
                save_filter_set(filter_name.strip(), st.session_state.current_filters)
                st.sidebar.success(f"Збережено: {filter_name}")
                st.rerun()
            else:
                st.sidebar.error("Введіть назву фільтру.")

    if saved:
        selected_saved = st.sidebar.selectbox(
            "Завантажити збережений",
            options=list(saved.keys()),
            key="saved_filter_select",
        )
        load_col, del_col = st.sidebar.columns(2)
        with load_col:
            if st.sidebar.button("Завантажити", key="btn_load_filter"):
                st.session_state.current_filters = saved[selected_saved]
                st.session_state.filters_applied = False
                for k in FILTER_WIDGET_KEYS:
                    st.session_state.pop(k, None)
                st.rerun()
        with del_col:
            if st.sidebar.button("Видалити", key="btn_del_filter"):
                delete_filter_set(selected_saved)
                st.rerun()

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------

st.title("📊 Аналіз цін і позиціонування")

if load_message:
    if "кешу" in load_message:
        st.success(f"✅ {load_message}")
    else:
        st.info(f"ℹ️ {load_message}")

if st.session_state.df_suppliers is None:
    st.info(
        "Завантажте файл бази постачальників у боковому меню.\n\n"
        "Тестові файли доступні у папці `test_data/`."
    )
    st.stop()

df_full = st.session_state.df_suppliers
st.caption(f"Загальна база: **{len(df_full):,}** рядків (В наявності > 0)")

if not st.session_state.filters_applied:
    if not st.session_state.current_filters.get("class"):
        st.warning("Оберіть **Клас** у боковому меню та натисніть «Застосувати фільтри».")
    else:
        st.info("Натисніть **«Застосувати фільтри»** у боковому меню для отримання результатів.")
    st.stop()

# Apply filters
df_filtered = apply_filters(df_full, st.session_state.current_filters)

if df_filtered.empty:
    st.warning("За обраними фільтрами нічого не знайдено. Змініть фільтри.")
    st.stop()

# ---------------------------------------------------------------------------
# Metrics row
# ---------------------------------------------------------------------------

wholesale_col = _col(df_filtered, "Исходная оптовая цена", "Вихідна оптова ціна")
supplier_col = _col(df_filtered, "Поставщик", "Постачальник")

st.subheader("Загальна статистика")
m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.metric("Позицій", f"{len(df_filtered):,}")
with m2:
    n_suppliers = df_filtered[supplier_col].nunique() if supplier_col else "—"
    st.metric("Постачальників", n_suppliers)
with m3:
    if wholesale_col:
        prices = pd.to_numeric(df_filtered[wholesale_col], errors="coerce").dropna()
        st.metric("Мін. оптова", f"{prices.min():,.0f} грн" if len(prices) else "—")
    else:
        st.metric("Мін. оптова", "—")
with m4:
    if wholesale_col:
        st.metric("Макс. оптова", f"{prices.max():,.0f} грн" if len(prices) else "—")
    else:
        st.metric("Макс. оптова", "—")
with m5:
    if wholesale_col:
        st.metric("Сер. оптова", f"{prices.mean():,.0f} грн" if len(prices) else "—")
    else:
        st.metric("Сер. оптова", "—")

st.divider()

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

st.subheader("Графіки")
_build_charts(df_filtered)

st.divider()

# ---------------------------------------------------------------------------
# Data table + export
# ---------------------------------------------------------------------------

st.subheader("Таблиця результатів")

display_cols = _table_columns(df_filtered)
df_display = df_filtered[display_cols] if display_cols else df_filtered

export_col, _ = st.columns([2, 6])
with export_col:
    excel_bytes = _export_excel(df_display)
    st.download_button(
        label="⬇️ Завантажити Excel",
        data=excel_bytes,
        file_name="analysis_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

_display_table(df_display, page_key="analysis_page")
