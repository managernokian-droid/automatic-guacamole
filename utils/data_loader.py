"""Data loading with Parquet cache and invalidation."""
import json
import os
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st

CACHE_DIR = "cache"
CACHE_META = os.path.join(CACHE_DIR, "meta_suppliers.json")
CACHE_PARQUET = os.path.join(CACHE_DIR, "suppliers.parquet")
CACHE_META_NOKIAN = os.path.join(CACHE_DIR, "meta_nokian.json")
CACHE_PARQUET_NOKIAN = os.path.join(CACHE_DIR, "nokian.parquet")

# Columns to convert to float32 after loading (errors='coerce' handles text/empty cells)
FLOAT32_COLS = [
    "Ширина профиля", "Высота профиля",
    "Исходная оптовая цена", "Исходная розничная цена",
    "Ширина профілю", "Висота профілю",
    "Вихідна оптова ціна", "Вихідна роздрібна ціна",
]

# Columns to convert to nullable int after loading
INT32_COLS = ["ID товара", "ID Поставщика", "В наличии", "ID товару", "ID Постачальника", "В наявності"]
INT16_COLS = ["Год изготовления шин", "Рік виготовлення шин"]

CATEGORY_COLS_RU = [
    "Бренд", "Класс", "Модель", "Сезон", "Поставщик",
    "Город", "Тип транспортного средства", "Усиление",
    "Шип/не шип", "Страна производитель",
]

CATEGORY_COLS_UA = [
    "Бренд", "Клас", "Модель", "Сезон", "Постачальник",
    "Місто", "Тип транспортного засобу", "Посилення",
    "Шип/не шип", "Країна виробник",
]


def _load_meta(meta_path: str) -> dict:
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_meta(meta_path: str, filename: str, filesize: int) -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
    meta = {
        "filename": filename,
        "filesize": filesize,
        "loaded_at": datetime.now().isoformat(),
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def _apply_categories(df: pd.DataFrame) -> pd.DataFrame:
    for col in CATEGORY_COLS_RU + CATEGORY_COLS_UA:
        if col in df.columns:
            df[col] = df[col].astype("category")
    return df


def _coerce_numeric_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Convert numeric columns with errors='coerce' to handle text/empty cells."""
    for col in FLOAT32_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("float32")
    for col in INT32_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int32")
    for col in INT16_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int16")
    return df


def load_suppliers(uploaded_file, force_reload: bool = False) -> tuple[pd.DataFrame, str]:
    """Load suppliers base from uploaded Excel. Returns (df, message)."""
    filename = uploaded_file.name
    filesize = uploaded_file.size

    meta = _load_meta(CACHE_META)
    cache_valid = (
        not force_reload
        and meta.get("filename") == filename
        and meta.get("filesize") == filesize
        and os.path.exists(CACHE_PARQUET)
    )

    if cache_valid:
        df = pd.read_parquet(CACHE_PARQUET)
        loaded_at = meta.get("loaded_at", "")
        try:
            dt = datetime.fromisoformat(loaded_at)
            date_str = dt.strftime("%d.%m.%Y %H:%M")
        except Exception:
            date_str = loaded_at
        return df, f"Дані завантажено з кешу ({date_str})"

    raw_bytes = uploaded_file.read()
    # Load all columns as default types — no dtype= to avoid ValueError on mixed cells
    df = pd.read_excel(BytesIO(raw_bytes))
    df = _coerce_numeric_cols(df)
    df = _apply_categories(df)

    # Filter out rows with 0 stock — detect column name
    stock_col = next(
        (c for c in ["В наличии", "В наявності"] if c in df.columns), None
    )
    if stock_col:
        df = df[df[stock_col] > 0].reset_index(drop=True)

    os.makedirs(CACHE_DIR, exist_ok=True)
    df.to_parquet(CACHE_PARQUET, index=False)
    _save_meta(CACHE_META, filename, filesize)

    return df, "Дані оновлено з файлу"


def load_nokian(uploaded_file, force_reload: bool = False) -> tuple[pd.DataFrame, str]:
    """Load Nokian price list from uploaded Excel. Returns (df, message)."""
    filename = uploaded_file.name
    filesize = uploaded_file.size

    meta = _load_meta(CACHE_META_NOKIAN)
    cache_valid = (
        not force_reload
        and meta.get("filename") == filename
        and meta.get("filesize") == filesize
        and os.path.exists(CACHE_PARQUET_NOKIAN)
    )

    if cache_valid:
        df = pd.read_parquet(CACHE_PARQUET_NOKIAN)
        loaded_at = meta.get("loaded_at", "")
        try:
            dt = datetime.fromisoformat(loaded_at)
            date_str = dt.strftime("%d.%m.%Y %H:%M")
        except Exception:
            date_str = loaded_at
        return df, f"Прайс Nokian завантажено з кешу ({date_str})"

    raw_bytes = uploaded_file.read()
    df = pd.read_excel(BytesIO(raw_bytes))

    os.makedirs(CACHE_DIR, exist_ok=True)
    df.to_parquet(CACHE_PARQUET_NOKIAN, index=False)
    _save_meta(CACHE_META_NOKIAN, filename, filesize)

    return df, "Прайс Nokian оновлено з файлу"


def clear_cache() -> None:
    """Remove all cached Parquet and meta files."""
    for path in [CACHE_PARQUET, CACHE_META, CACHE_PARQUET_NOKIAN, CACHE_META_NOKIAN]:
        if os.path.exists(path):
            os.remove(path)
