"""Phase 3 stub — Price dynamics analysis."""
import streamlit as st

st.set_page_config(
    page_title="Динаміка цін — Nokian",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Динаміка цін")
st.info(
    "**Модуль динаміки цін — в розробці (Фаза 3)**\n\n"
    "Планується:\n"
    "- Аналіз зміни цін у часі\n"
    "- Порівняння поточних і попередніх завантажень\n"
    "- Прогнозування трендів (scikit-learn, scipy)\n"
    "- Перехід до зберігання даних у DuckDB"
)
