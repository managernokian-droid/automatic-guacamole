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

SUPPLIERS_DTYPE = {
    "ID товару": "int32",
    "ID Постачальника": "int32",
    "В наявності": "int32",
    "Рік виготовлення шин": "Int16",
    "Ширина профілю": "float32",
    "Висота профілю": "float32",
    "Діаметр": "float32",
    "Вихідна оптова ціна": "float32",
    "Вихідна роздрібна ціна": "float32",
}

SUPPLIERS_DTYPE_RU = {
    "ID товара": "int32",
    "ID Поставщика": "int32",
    "В наличии": "int32",
    "Год изготовления шин": "Int16",
    "Ширина профиля": "float32",
    "Высота профиля": "float32",
    "Диаметр": "float32",
    "Исходная оптовая цена": "float32",
    "Исходная розничная цена": "float32",
}

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


def _detect_dtype_map(df: pd.DataFrame) -> dict:
    """Return dtype map matching the columns actually present in df."""
    combined = {**SUPPLIERS_DTYPE_RU, **SUPPLIERS_DTYPE}
    return {k: v for k, v in combined.items() if k in df.columns}


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
    # Read without forced dtype first to detect column names
    df_probe = pd.read_excel(BytesIO(raw_bytes), nrows=0)
    dtype_map = _detect_dtype_map(df_probe)

    df = pd.read_excel(BytesIO(raw_bytes), dtype=dtype_map)
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
