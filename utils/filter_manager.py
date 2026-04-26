"""Cascade smart filter management with session state persistence."""
import json
import os

import pandas as pd
import streamlit as st

SAVED_FILTERS_PATH = "data/saved_filters.json"


def _col(df: pd.DataFrame, *candidates) -> str | None:
    """Return first column name from candidates that exists in df."""
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _value_counts_label(series: pd.Series) -> list[str]:
    """Return sorted list of 'Value (N)' strings."""
    counts = series.value_counts().sort_index()
    return [f"{v} ({counts[v]:,})" for v in counts.index]


def _strip_count(label: str) -> str:
    """Strip count suffix: 'Nokian (123)' → 'Nokian'."""
    if " (" in label:
        return label[: label.rfind(" (")]
    return label


def render_cascade_filters(df: pd.DataFrame) -> dict:
    """
    Render cascade filters in st.sidebar.
    Returns dict of applied filter values (raw, without count labels).
    """
    filters = {}
    current = df.copy()

    # --- 1. Клас (mandatory) ---
    class_col = _col(df, "Класс", "Клас")
    if class_col:
        available = sorted(current[class_col].dropna().astype(str).unique())
        labels = [f"{v} ({(current[class_col].astype(str) == v).sum():,})" for v in available]
        saved_class = st.session_state.current_filters.get("class", [])
        saved_labels = [l for l in labels if _strip_count(l) in saved_class]
        sel_labels = st.sidebar.multiselect(
            "Клас (обов'язково)",
            options=labels,
            default=saved_labels,
            key="filter_class",
        )
        sel = [_strip_count(l) for l in sel_labels]
        filters["class"] = sel
        if sel:
            current = current[current[class_col].astype(str).isin(sel)]
    else:
        filters["class"] = []

    # --- 2. Сезон ---
    season_col = _col(df, "Сезон")
    if season_col:
        available = sorted(current[season_col].dropna().astype(str).unique())
        labels = [f"{v} ({(current[season_col].astype(str) == v).sum():,})" for v in available]
        saved = st.session_state.current_filters.get("season", [])
        saved_labels = [l for l in labels if _strip_count(l) in saved]
        sel_labels = st.sidebar.multiselect("Сезон", options=labels, default=saved_labels, key="filter_season")
        sel = [_strip_count(l) for l in sel_labels]
        filters["season"] = sel
        if sel:
            current = current[current[season_col].astype(str).isin(sel)]
    else:
        filters["season"] = []

    # --- 3. Рік виготовлення ---
    year_col = _col(df, "Год изготовления шин", "Рік виготовлення шин")
    if year_col:
        available = sorted(current[year_col].dropna().unique(), reverse=True)
        available_str = [str(int(v)) if str(v).endswith(".0") else str(v) for v in available]
        labels = [f"{v} ({(current[year_col] == raw).sum():,})" for v, raw in zip(available_str, available)]
        saved = st.session_state.current_filters.get("year", [])
        saved_labels = [l for l in labels if _strip_count(l) in saved]
        sel_labels = st.sidebar.multiselect("Рік виготовлення", options=labels, default=saved_labels, key="filter_year")
        sel = [_strip_count(l) for l in sel_labels]
        filters["year"] = sel
        if sel:
            current = current[current[year_col].astype(str).str.replace(r"\.0$", "", regex=True).isin(sel)]
    else:
        filters["year"] = []

    # --- 4. Тип транспортного засобу ---
    type_col = _col(df, "Тип транспортного средства", "Тип транспортного засобу")
    if type_col:
        available = sorted(current[type_col].dropna().astype(str).unique())
        labels = [f"{v} ({(current[type_col].astype(str) == v).sum():,})" for v in available]
        saved = st.session_state.current_filters.get("vehicle_type", [])
        saved_labels = [l for l in labels if _strip_count(l) in saved]
        sel_labels = st.sidebar.multiselect("Тип ТЗ", options=labels, default=saved_labels, key="filter_vehicle_type")
        sel = [_strip_count(l) for l in sel_labels]
        filters["vehicle_type"] = sel
        if sel:
            current = current[current[type_col].astype(str).isin(sel)]
    else:
        filters["vehicle_type"] = []

    # --- 5. Бренд ---
    brand_col = _col(df, "Бренд")
    if brand_col:
        available = sorted(current[brand_col].dropna().astype(str).unique())
        labels = [f"{v} ({(current[brand_col].astype(str) == v).sum():,})" for v in available]
        saved = st.session_state.current_filters.get("brand", [])
        saved_labels = [l for l in labels if _strip_count(l) in saved]
        sel_labels = st.sidebar.multiselect("Бренд", options=labels, default=saved_labels, key="filter_brand")
        sel = [_strip_count(l) for l in sel_labels]
        filters["brand"] = sel
        if sel:
            current = current[current[brand_col].astype(str).isin(sel)]
    else:
        filters["brand"] = []

    # --- 6. Постачальник ---
    supplier_col = _col(df, "Поставщик", "Постачальник")
    if supplier_col:
        available = sorted(current[supplier_col].dropna().astype(str).unique())
        labels = [f"{v} ({(current[supplier_col].astype(str) == v).sum():,})" for v in available]
        saved = st.session_state.current_filters.get("supplier", [])
        saved_labels = [l for l in labels if _strip_count(l) in saved]
        sel_labels = st.sidebar.multiselect("Постачальник", options=labels, default=saved_labels, key="filter_supplier")
        sel = [_strip_count(l) for l in sel_labels]
        filters["supplier"] = sel
        if sel:
            current = current[current[supplier_col].astype(str).isin(sel)]
    else:
        filters["supplier"] = []

    # --- 7. Модель ---
    model_col = _col(df, "Модель")
    if model_col:
        available = sorted(current[model_col].dropna().astype(str).unique())
        labels = [f"{v} ({(current[model_col].astype(str) == v).sum():,})" for v in available]
        saved = st.session_state.current_filters.get("model", [])
        saved_labels = [l for l in labels if _strip_count(l) in saved]
        sel_labels = st.sidebar.multiselect("Модель", options=labels, default=saved_labels, key="filter_model")
        sel = [_strip_count(l) for l in sel_labels]
        filters["model"] = sel
        if sel:
            current = current[current[model_col].astype(str).isin(sel)]
    else:
        filters["model"] = []

    # --- 8. Шип/не шип ---
    stud_col = _col(df, "Шип/не шип")
    if stud_col:
        available = sorted(current[stud_col].dropna().astype(str).unique())
        labels = [f"{v} ({(current[stud_col].astype(str) == v).sum():,})" for v in available]
        saved = st.session_state.current_filters.get("studded", [])
        saved_labels = [l for l in labels if _strip_count(l) in saved]
        sel_labels = st.sidebar.multiselect("Шип/не шип", options=labels, default=saved_labels, key="filter_studded")
        sel = [_strip_count(l) for l in sel_labels]
        filters["studded"] = sel
        if sel:
            current = current[current[stud_col].astype(str).isin(sel)]
    else:
        filters["studded"] = []

    # --- 9. Місто ---
    city_col = _col(df, "Город", "Місто")
    if city_col:
        available = sorted(current[city_col].dropna().astype(str).unique())
        labels = [f"{v} ({(current[city_col].astype(str) == v).sum():,})" for v in available]
        saved = st.session_state.current_filters.get("city", [])
        saved_labels = [l for l in labels if _strip_count(l) in saved]
        sel_labels = st.sidebar.multiselect("Місто", options=labels, default=saved_labels, key="filter_city")
        sel = [_strip_count(l) for l in sel_labels]
        filters["city"] = sel
        if sel:
            current = current[current[city_col].astype(str).isin(sel)]
    else:
        filters["city"] = []

    return filters


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Apply filter dict to df using boolean masks."""
    col_map = {
        "class": ["Класс", "Клас"],
        "season": ["Сезон"],
        "year": ["Год изготовления шин", "Рік виготовлення шин"],
        "vehicle_type": ["Тип транспортного средства", "Тип транспортного засобу"],
        "brand": ["Бренд"],
        "supplier": ["Поставщик", "Постачальник"],
        "model": ["Модель"],
        "studded": ["Шип/не шип"],
        "city": ["Город", "Місто"],
    }

    mask = pd.Series(True, index=df.index)
    for key, candidates in col_map.items():
        values = filters.get(key, [])
        if not values:
            continue
        col = next((c for c in candidates if c in df.columns), None)
        if col:
            if key == "year":
                year_str = df[col].astype(str).str.replace(r"\.0$", "", regex=True)
                mask &= year_str.isin(values)
            else:
                mask &= df[col].astype(str).isin(values)
    return df[mask].copy()


def load_saved_filters() -> dict:
    if os.path.exists(SAVED_FILTERS_PATH):
        try:
            with open(SAVED_FILTERS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_filter_set(name: str, filters: dict) -> None:
    saved = load_saved_filters()
    saved[name] = filters
    os.makedirs("data", exist_ok=True)
    with open(SAVED_FILTERS_PATH, "w", encoding="utf-8") as f:
        json.dump(saved, f, ensure_ascii=False, indent=2)


def delete_filter_set(name: str) -> None:
    saved = load_saved_filters()
    saved.pop(name, None)
    with open(SAVED_FILTERS_PATH, "w", encoding="utf-8") as f:
        json.dump(saved, f, ensure_ascii=False, indent=2)
