"""Phase 2 stub — Price monitoring with Nokian price list and Telegram."""
import streamlit as st

st.set_page_config(
    page_title="Моніторинг — Nokian",
    page_icon="🔔",
    layout="wide",
)

st.title("🔔 Моніторинг цін Nokian")
st.info(
    "**Модуль моніторингу — в розробці (Фаза 2)**\n\n"
    "Цей модуль дозволить:\n"
    "- Порівнювати ціни постачальників з рекомендованим прайсом Nokian\n"
    "- Виявляти порушення (оптова ціна нижче рекомендованої)\n"
    "- Відправляти сповіщення постачальникам через Telegram Bot API\n"
    "- Вести журнал відправлених повідомлень\n\n"
    "Для активації модуля встановіть пакети з `requirements-advanced.txt`."
)

st.subheader("Заплановані функції")
col1, col2 = st.columns(2)
with col1:
    st.markdown(
        """
        **Аналіз порушень:**
        - Фільтри: Рік, Сезон, Клас, Постачальник
        - Таблиця порушень з відхиленнями (грн і %)
        - Діагностика незбіжних ключів матчингу
        """
    )
with col2:
    st.markdown(
        """
        **Telegram сповіщення:**
        - Управління контактами постачальників
        - Чекбокси для вибору порушників
        - Відправка тексту + Excel файлу через Bot API
        - Журнал відправлень у `data/notifications_log.json`
        """
    )

st.caption("Файли-заглушки вже створені: `utils/telegram_sender.py`, `data/telegram_contacts.json`")
