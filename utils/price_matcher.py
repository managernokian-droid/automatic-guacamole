"""Matching Nokian price list with suppliers base."""
import re

import pandas as pd


def normalize_col(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower()


def normalize_diameter(series: pd.Series) -> pd.Series:
    """Remove leading 'r' from diameter values: R17 → 17."""
    return (
        series.astype(str)
        .str.strip()
        .str.lower()
        .str.lstrip("r")
        .str.replace(r"\.0$", "", regex=True)
    )


def normalize_xl(series: pd.Series) -> pd.Series:
    """Normalize XL/reinforcement field to 'xl' or 'standard'."""
    s = series.astype(str).str.strip().str.lower()
    xl_mask = s.isin(["xl", "усил", "reinforced", "xl/усиленная", "усиленная"]) | s.str.startswith("xl")
    standard_mask = s.isin(["nan", "", "нет", "no", "false", "ні", "немає"])
    result = pd.Series("standard", index=series.index)
    result[xl_mask] = "xl"
    result[standard_mask] = "standard"
    return result


def parse_load_speed(series: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Parse '91W', 'W91', '91/W' into (load_index, speed_index)."""
    pattern = re.compile(r"(\d+)\s*[/]?\s*([a-zA-Z]+)|([a-zA-Z]+)\s*(\d+)")

    load_list, speed_list = [], []
    for val in series.astype(str):
        val = val.strip()
        m = re.match(r"^(\d+)\s*[/]?\s*([a-zA-Z]*)$", val)
        if m:
            load_list.append(m.group(1).lower())
            speed_list.append(m.group(2).lower() if m.group(2) else "")
            continue
        m2 = re.match(r"^([a-zA-Z]+)\s*(\d+)$", val)
        if m2:
            speed_list.append(m2.group(1).lower())
            load_list.append(m2.group(2).lower())
            continue
        load_list.append(val.lower())
        speed_list.append("")
    return pd.Series(load_list, index=series.index), pd.Series(speed_list, index=series.index)


def _make_key_suppliers(df: pd.DataFrame) -> pd.Series:
    brand_col = next((c for c in ["Бренд"] if c in df.columns), None)
    model_col = next((c for c in ["Модель"] if c in df.columns), None)
    width_col = next((c for c in ["Ширина профиля", "Ширина профілю"] if c in df.columns), None)
    height_col = next((c for c in ["Высота профиля", "Висота профілю"] if c in df.columns), None)
    diam_col = next((c for c in ["Диаметр", "Діаметр"] if c in df.columns), None)
    load_col = next((c for c in ["Индекс нагрузки", "Індекс навантаження"] if c in df.columns), None)
    speed_col = next((c for c in ["Индекс скорости", "Індекс швидкості"] if c in df.columns), None)
    xl_col = next((c for c in ["Усиление", "Посилення"] if c in df.columns), None)

    brand = normalize_col(df[brand_col]) if brand_col else pd.Series("", index=df.index)
    model = normalize_col(df[model_col]) if model_col else pd.Series("", index=df.index)
    width = normalize_col(df[width_col].astype(str).str.replace(r"\.0$", "", regex=True)) if width_col else pd.Series("", index=df.index)
    height = normalize_col(df[height_col].astype(str).str.replace(r"\.0$", "", regex=True)) if height_col else pd.Series("", index=df.index)
    diam = normalize_diameter(df[diam_col]) if diam_col else pd.Series("", index=df.index)
    xl = normalize_xl(df[xl_col]) if xl_col else pd.Series("standard", index=df.index)

    if load_col and speed_col:
        # Combine separate load + speed columns into "91W" style before parsing
        combined = (
            df[load_col].astype(str).str.strip()
            + df[speed_col].astype(str).str.strip()
        )
        load_s, speed_s = parse_load_speed(combined)
    elif load_col:
        load_s, speed_s = parse_load_speed(df[load_col])
    else:
        load_s = pd.Series("", index=df.index)
        speed_s = pd.Series("", index=df.index)

    return brand + "_" + model + "_" + width + "_" + height + "_" + diam + "_" + load_s + "_" + speed_s + "_" + xl


def _make_key_nokian(df: pd.DataFrame) -> pd.Series:
    brand = pd.Series("nokian", index=df.index)
    model_col = next((c for c in ["Продуктова група", "Продуктова группа"] if c in df.columns), None)
    width_col = next((c for c in ["Ширина"] if c in df.columns), None)
    height_col = next((c for c in ["Профіль", "Профиль"] if c in df.columns), None)
    diam_col = next((c for c in ["Діаметр", "Диаметр"] if c in df.columns), None)
    load_speed_col = next((c for c in ["Навант/Швид", "Индекс нагрузки/скорости"] if c in df.columns), None)
    xl_col = next((c for c in ["XL"] if c in df.columns), None)

    model = normalize_col(df[model_col]) if model_col else pd.Series("", index=df.index)
    width = normalize_col(df[width_col].astype(str).str.replace(r"\.0$", "", regex=True)) if width_col else pd.Series("", index=df.index)
    height = normalize_col(df[height_col].astype(str).str.replace(r"\.0$", "", regex=True)) if height_col else pd.Series("", index=df.index)
    diam = normalize_diameter(df[diam_col]) if diam_col else pd.Series("", index=df.index)
    xl = normalize_xl(df[xl_col]) if xl_col else pd.Series("standard", index=df.index)

    if load_speed_col:
        load_s, speed_s = parse_load_speed(df[load_speed_col])
    else:
        load_s = pd.Series("", index=df.index)
        speed_s = pd.Series("", index=df.index)

    return brand + "_" + model + "_" + width + "_" + height + "_" + diam + "_" + load_s + "_" + speed_s + "_" + xl


def match_prices(df_suppliers: pd.DataFrame, df_nokian: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Match suppliers base with Nokian price list.
    Returns (merged_df, diagnostics_dict).
    """
    df_sup = df_suppliers.copy()
    df_nok = df_nokian.copy()

    df_sup["match_key"] = _make_key_suppliers(df_sup)
    df_nok["match_key"] = _make_key_nokian(df_nok)

    merged = pd.merge(df_sup, df_nok, on="match_key", how="inner", suffixes=("_sup", "_nok"))

    # Detect price columns
    wholesale_col = next(
        (c for c in ["Исходная оптовая цена", "Вихідна оптова ціна"] if c in df_sup.columns), None
    )
    rec_price_col = next(
        (c for c in ["Рекомендована оптова ціна грн з ПДВ", "Рекомендованная оптовая цена грн с НДС"]
         if c in df_nok.columns), None
    )

    if wholesale_col and rec_price_col:
        ws_col_merged = wholesale_col if wholesale_col in merged.columns else wholesale_col + "_sup"
        rec_col_merged = rec_price_col if rec_price_col in merged.columns else rec_price_col + "_nok"

        if ws_col_merged in merged.columns and rec_col_merged in merged.columns:
            merged["відхилення_грн"] = (
                pd.to_numeric(merged[ws_col_merged], errors="coerce")
                - pd.to_numeric(merged[rec_col_merged], errors="coerce")
            ).round(2)
            merged["відхилення_%"] = (
                merged["відхилення_грн"]
                / pd.to_numeric(merged[rec_col_merged], errors="coerce")
                * 100
            ).round(2)

    total_nokian = len(df_nok)
    matched_nokian = df_nok["match_key"].isin(merged["match_key"]).sum() if not merged.empty else 0
    match_ratio = matched_nokian / total_nokian if total_nokian > 0 else 0

    unmatched_sup_keys = df_sup[~df_sup["match_key"].isin(df_nok["match_key"])]["match_key"].dropna().unique()[:10]
    unmatched_nok_keys = df_nok[~df_nok["match_key"].isin(df_sup["match_key"])]["match_key"].dropna().unique()[:10]

    diagnostics = {
        "total_suppliers_rows": len(df_sup),
        "total_nokian_rows": total_nokian,
        "matched_rows": len(merged),
        "match_ratio": match_ratio,
        "low_match_warning": match_ratio < 0.05 and total_nokian > 0,
        "sample_unmatched_suppliers": list(unmatched_sup_keys),
        "sample_unmatched_nokian": list(unmatched_nok_keys),
    }

    return merged, diagnostics


def get_violations(merged: pd.DataFrame) -> pd.DataFrame:
    """Return rows where wholesale price < recommended price - 1 UAH."""
    if "відхилення_грн" not in merged.columns:
        return pd.DataFrame()
    return merged[merged["відхилення_грн"] < -1].copy()
