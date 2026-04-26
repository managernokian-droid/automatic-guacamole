"""Generate realistic test data for Nokian tire analysis app."""
import random
import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

# --- Nokian price list (50 positions) ---
nokian_models = [
    "Hakka Blue 2", "Hakka Green 3", "Hakka Black 2", "Hakka Van 2",
    "Nordman 8", "Nordman 7", "Nordman 5", "Nordman RS2",
    "Hakka SUV 2", "Hakka 9",
]
seasons = ["Літо", "Зима", "Всесезон"]
sizes_summer = [
    (195, 65, 15, "91", "V"), (205, 55, 16, "91", "W"), (215, 60, 16, "99", "H"),
    (225, 45, 17, "91", "W"), (235, 55, 17, "99", "V"), (175, 65, 14, "82", "T"),
    (185, 65, 15, "88", "T"), (195, 60, 15, "88", "H"), (205, 50, 17, "93", "W"),
    (225, 40, 18, "92", "Y"),
]
sizes_winter = [
    (205, 55, 16, "94", "T"), (215, 65, 16, "98", "T"), (185, 65, 15, "92", "T"),
    (195, 65, 15, "95", "T"), (225, 50, 17, "98", "T"), (235, 65, 17, "108", "T"),
    (175, 70, 13, "82", "T"), (205, 60, 16, "96", "T"), (245, 45, 18, "100", "T"),
    (265, 65, 17, "116", "T"),
]

nokian_rows = []
used_sizes = set()

for _ in range(50):
    model = random.choice(nokian_models)
    season = "Зима" if "Nordman" in model or "8" in model or "7" in model else random.choice(["Літо", "Всесезон"])
    sizes = sizes_winter if season == "Зима" else sizes_summer
    size = random.choice(sizes)
    w, h, d, li, si = size
    xl = random.choice(["", "XL", "XL", ""])
    key = (model, w, h, d, li, si, xl)
    if key in used_sizes:
        continue
    used_sizes.add(key)

    sku = f"T{random.randint(100000, 999999)}"
    ean = str(random.randint(4000000000000, 4999999999999))
    size_str = f"{w}/{h}R{d}"
    load_speed = f"{li}{si}"
    rrc = random.choice(["A", "B", "C"])
    wgc = random.choice(["A", "B", "C"])
    noc = random.randint(68, 74)
    db = random.randint(68, 74)
    base_price = round(random.uniform(1200, 8000), 2)

    nokian_rows.append({
        "Сезон": season,
        "Артикул": sku,
        "EAN": ean,
        "Розмір": size_str,
        "Ширина": w,
        "Профіль": h,
        "Діаметр": f"R{d}",
        "Навант/Швид": load_speed,
        "XL": xl,
        "Продуктова група": model,
        "Продуктова група з деталізацією": f"{model} {size_str}",
        "RRC": rrc,
        "WGC": wgc,
        "NOC": noc,
        "dB": db,
        "Рекомендована оптова ціна грн з ПДВ": base_price,
    })

df_nokian = pd.DataFrame(nokian_rows[:50])

# --- Suppliers base (500 rows) ---
suppliers = [
    ("АвтоШина Плюс", "Київ"), ("ТайрМаркет", "Харків"), ("ШинТрейд", "Одеса"),
    ("КолесоПро", "Дніпро"), ("Тирекс UA", "Львів"), ("ШинСервіс", "Запоріжжя"),
    ("АвтоРезина", "Маріуполь"), ("ДрайвШина", "Вінниця"), ("ТайрЛенд", "Полтава"),
    ("ШинОпт", "Рівне"), ("КолесоМаркет", "Чернігів"), ("РезинаПлюс", "Суми"),
    ("ШинЦентр", "Хмельницький"), ("ТайрПро", "Херсон"), ("АвтоКолесо", "Житомир"),
]

brands = (
    ["Nokian"] * 6 + ["Michelin", "Continental", "Nexen", "Bridgestone"]
)
classes = {
    "Nokian": "Premium", "Michelin": "Premium", "Continental": "Premium",
    "Bridgestone": "Premium", "Nexen": "Mid", "Semperit": "Mid",
    "Hankook": "Mid", "Toyo": "Mid", "Kumho": "Econom+", "Maxxis": "Econom+",
    "Formula": "Econom",
}

nokian_model_variants = {
    "Hakka Blue 2": ["Hakka Blue 2", "HAKKA BLUE 2", "hakka blue 2"],
    "Hakka Green 3": ["Hakka Green 3", "HAKKA GREEN 3"],
    "Nordman 8": ["Nordman 8", "NORDMAN 8"],
    "Nordman 7": ["Nordman 7", "nordman 7"],
    "Hakka Black 2": ["Hakka Black 2", "HAKKA BLACK 2"],
    "Nordman 5": ["Nordman 5"],
    "Nordman RS2": ["Nordman RS2", "Nordman RS 2"],
    "Hakka SUV 2": ["Hakka SUV 2", "HAKKA SUV 2"],
    "Hakka 9": ["Hakka 9"],
    "Hakka Van 2": ["Hakka Van 2"],
}
other_models = {
    "Michelin": ["Pilot Sport 4", "Energy Saver+", "CrossClimate 2", "Primacy 4"],
    "Continental": ["PremiumContact 6", "SportContact 7", "AllSeasonContact"],
    "Nexen": ["N'Blue HD Plus", "Roadian HTX RH5", "Winguard Sport 2"],
    "Bridgestone": ["Turanza T005", "Potenza Sport", "Blizzak LM005"],
}

diameter_formats = [
    lambda d: str(d),
    lambda d: f"R{d}",
    lambda d: f"r{d}",
]

xl_formats = ["", "XL", np.nan, "XL", ""]
load_speed_formats = [
    lambda li, si: f"{li}{si}",
    lambda li, si: f"{li}/{si}",
    lambda li, si: f"{si}{li}",
    lambda li, si: str(li),
]

rows = []
vehicle_types = ["Легковий", "Позашляховик", "Мікроавтобус"]
stud_options = ["Не шипований", "Шипований", "Не шипований"]

for i in range(500):
    brand = random.choice(brands)
    sup_name, city = random.choice(suppliers)

    if brand == "Nokian":
        model_key = random.choice(list(nokian_model_variants.keys()))
        model = random.choice(nokian_model_variants[model_key])
        season_map = {"Nordman": "Зима", "Hakka Blue": "Літо", "Hakka Green": "Літо",
                      "Hakka Black": "Літо", "Hakka SUV": "Літо", "Nordman RS": "Зима",
                      "Hakka 9": "Літо", "Hakka Van": "Літо"}
        season = next((v for k, v in season_map.items() if k in model_key), "Літо")
        cls = "Premium"
    else:
        cls = classes.get(brand, "Mid")
        model_list = other_models.get(brand, ["Model A", "Model B"])
        model = random.choice(model_list)
        season = random.choice(["Літо", "Зима", "Всесезон"])

    sizes_pool = sizes_summer if season == "Літо" else sizes_winter
    w, h, d, li, si = random.choice(sizes_pool)[:5]

    diam_fn = random.choice(diameter_formats)
    diam_str = diam_fn(d)

    xl = random.choice(xl_formats)
    xl_display = xl if xl is not np.nan else np.nan

    load_fn = random.choice(load_speed_formats)
    load_speed = load_fn(li, si)

    year = random.choice([2021, 2022, 2023, 2024])
    stock = random.choice([0, 0, 1, 2, 4, 8, 12, 20, 50])
    vehicle_type = random.choice(vehicle_types)
    stud = random.choice(stud_options)

    wholesale_base = round(random.uniform(900, 7500), 2)
    retail = round(wholesale_base * random.uniform(1.15, 1.35), 2)

    # 10-15 Nokian rows with prices BELOW Nokian recommended (for monitoring test)
    if brand == "Nokian" and i < 60 and random.random() < 0.25:
        # Find matching Nokian price and set wholesale lower
        matching = df_nokian[
            (df_nokian["Ширина"] == w) &
            (df_nokian["Профіль"] == h) &
            (df_nokian["Навант/Швид"].str.contains(str(li), na=False))
        ]
        if not matching.empty:
            rec_price = matching.iloc[0]["Рекомендована оптова ціна грн з ПДВ"]
            wholesale_base = round(rec_price * random.uniform(0.7, 0.95), 2)
            retail = round(wholesale_base * 1.2, 2)

    full_name = f"{brand} {model} {w}/{h}R{d} {li}{si}"
    if xl == "XL":
        full_name += " XL"

    rows.append({
        "ID товара": i + 1,
        "ID Поставщика": suppliers.index((sup_name, city)) + 1,
        "Бренд": brand,
        "Класс": cls,
        "Модель": model,
        "Полное название": full_name,
        "Сезон": season,
        "Ширина профиля": float(w),
        "Высота профиля": float(h),
        "Диаметр": diam_str,
        "Индекс нагрузки": str(li),
        "Индекс скорости": si,
        "Усиление": xl_display,
        "Шип/не шип": stud,
        "Страна производитель": "Фінляндія" if brand == "Nokian" else random.choice(["Германія", "Польща", "Корея", "Японія"]),
        "Дата обновления": f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
        "Поставщик": sup_name,
        "Город": city,
        "В наличии": stock,
        "Исходная оптовая цена": wholesale_base,
        "Исходная розничная цена": retail,
        "Тип транспортного средства": vehicle_type,
        "Год изготовления шин": year,
        "Омологация": "",
    })

df_suppliers = pd.DataFrame(rows)

# Save to Excel
with pd.ExcelWriter("test_data/suppliers_base.xlsx", engine="openpyxl") as writer:
    df_suppliers.to_excel(writer, index=False, sheet_name="Sheet1")

with pd.ExcelWriter("test_data/nokian_price.xlsx", engine="openpyxl") as writer:
    df_nokian.to_excel(writer, index=False, sheet_name="Sheet1")

print(f"suppliers_base.xlsx: {len(df_suppliers)} rows")
print(f"nokian_price.xlsx: {len(df_nokian)} rows")
print("Done.")
