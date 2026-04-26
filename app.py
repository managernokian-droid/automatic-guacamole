"""Nokian Tire Price Analysis — main entry point."""
import streamlit as st

st.set_page_config(
    page_title="Аналіз цін шин Nokian",
    page_icon="🛞",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Session state initialization ---
if "df_suppliers" not in st.session_state:
    st.session_state.df_suppliers = None
if "df_nokian" not in st.session_state:
    st.session_state.df_nokian = None
if "filters_applied" not in st.session_state:
    st.session_state.filters_applied = False
if "current_filters" not in st.session_state:
    st.session_state.current_filters = {}
if "language" not in st.session_state:
    st.session_state.language = "ua"

# --- Home page ---
st.title("🛞 Аналіз цін шин Nokian")

st.markdown(
    """
    Ласкаво просимо до системи аналізу цін шин Nokian.

    ### Навігація
    Використовуйте бокове меню для переходу між модулями:

    | Модуль | Статус | Опис |
    |--------|--------|------|
    | **📊 Аналіз цін** | ✅ Готово | Фільтрація, графіки, експорт Excel |
    | **🔔 Моніторинг** | 🔧 Фаза 2 | Порівняння з прайсом Nokian, Telegram |
    | **📈 Динаміка цін** | 🔧 Фаза 3 | Аналіз тенденцій |
    | **💰 Нетто-ціни** | 🔧 Фаза 3 | Розрахунок нетто |

    ### Швидкий старт
    1. Перейдіть до **📊 Аналіз цін**
    2. Завантажте базу постачальників (Excel)
    3. Оберіть фільтри та натисніть «Застосувати фільтри»
    4. Аналізуйте дані та завантажуйте звіти

    ### Тестові дані
    Готові тестові файли знаходяться у папці `test_data/`:
    - `suppliers_base.xlsx` — 500 позицій від 15 постачальників
    - `nokian_price.xlsx` — прайс Nokian (43 позиції)
    """
)

st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.info("**Фаза 1 — Готово**\n\nАналіз цін і позиціонування з фільтрами, графіками та експортом.")
with col2:
    st.warning("**Фаза 2 — В розробці**\n\nМоніторинг цін Nokian з відправкою сповіщень через Telegram.")
with col3:
    st.warning("**Фаза 3 — Планується**\n\nАвторизація, мультимовність (UA/RU/EN), динаміка цін.")
