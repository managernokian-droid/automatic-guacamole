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

# float32: replace comma decimal separator, then coerce
FLOAT32_COLS = [
    "Ширина профиля", "Высота профиля", "Диаметр",
    "Исходная оптовая цена", "Исходная розничная цена",
    "Ширина профілю", "Висота профілю", "Діаметр",
    "Вихідна оптова ціна", "Вихідна роздрібна ціна",
]

# Int16: nullable (may have empty cells)
INT16_COLS = ["Год изготовления шин", "Рік виготовлення шин"]

# int32: fillna(0) — stock and IDs must be whole numbers
INT32_COLS = ["ID товара", "ID Поставщика", "В наличии", "ID товару", "ID Постачальника", "В наявності"]

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


def _save_parquet(df: pd.DataFrame, path: str) -> None:
    """Save df to Parquet, converting category columns to str first.

    pyarrow cannot serialize mixed-type category columns (e.g. str + float
    category values produce ArrowInvalid). We store as plain str and restore
    categories after reading from cache.
    """
    df_to_save = df.copy()
    for col in df_to_save.select_dtypes(include="category").columns:
        df_to_save[col] = df_to_save[col].astype(str)
    df_to_save.to_parquet(path, index=False)


def _coerce_numeric_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Convert numeric columns tolerating comma decimals, text, and empty cells."""
    for col in FLOAT32_COLS:
        if col in df.columns:
            df[col] = (
                df[col].astype(str).str.replace(",", ".", regex=False)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("float32")
    for col in INT16_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int16")
    for col in INT32_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype("int32")
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
        df = _apply_categories(df)
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
    _save_parquet(df, CACHE_PARQUET)
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
        df = _apply_categories(df)
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
    _save_parquet(df, CACHE_PARQUET_NOKIAN)
    _save_meta(CACHE_META_NOKIAN, filename, filesize)

    return df, "Прайс Nokian оновлено з файлу"


def clear_cache() -> None:
    """Remove all cached Parquet and meta files."""
    for path in [CACHE_PARQUET, CACHE_META, CACHE_PARQUET_NOKIAN, CACHE_META_NOKIAN]:
        if os.path.exists(path):
            os.remove(path)
