"""Lectura y validación de los agregados de Athena en formato CSV.

Cada CSV corresponde a una agregación independiente sobre el mismo universo de
transacciones. NO se pueden cruzar filtros de una dimensión con otra sin datos
microgranulares o SQL adicional.
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "Athena · resultados exportados (AWS)": ROOT / "data" / "athena_results",
    "Previsualización local · no es AWS": ROOT / "data" / "local_preview",
}
DATASETS = {
    "01": ("Resumen global", "01_kpis_fraude.csv"),
    "02": ("Monto winsorizado", "02_fraude_por_monto.csv"),
    "03": ("Noche frente a día", "03_fraude_noche.csv"),
    "04": ("Categoría de riesgo", "04_fraude_categoria_riesgo.csv"),
    "05": ("Edad", "05_fraude_edad.csv"),
    "06": ("Mes", "06_fraude_mes.csv"),
    "07": ("Fin de semana", "07_fraude_fin_semana.csv"),
    "08": ("Distancia", "08_fraude_por_distancia.csv"),
}


def load_tables(source: str) -> dict[str, pd.DataFrame]:
    if source not in SOURCES:
        raise ValueError(f"Fuente desconocida: {source}")
    directory = SOURCES[source]
    tables = {}
    for code, (_name, filename) in DATASETS.items():
        path = directory / filename
        if not path.is_file():
            raise FileNotFoundError(f"Falta {path.relative_to(ROOT)}")
        tables[code] = pd.read_csv(path)
    return tables


def validate_tables(tables: dict[str, pd.DataFrame]) -> list[str]:
    """Devuelve errores de consistencia sin cambiar los datos originales."""
    errors = []
    k = tables["01"].iloc[0]
    total = int(k["total_transacciones"])
    frauds = int(k["transacciones_fraude"])
    legit = int(k["transacciones_legitimas"])
    if total != frauds + legit:
        errors.append("Fraudes + legítimas no coincide con total")
    if abs(100 * frauds / total - float(k["tasa_fraude_pct"])) > 0.0001:
        errors.append("La tasa global calculada no coincide")
    for code, frame in tables.items():
        if code == "01":
            continue
        expected = {"transacciones", "fraudes", "tasa_fraude_pct"}
        if not expected.issubset(frame.columns):
            errors.append(f"Faltan columnas de agregación en {code}")
            continue
        if int(frame["transacciones"].sum()) != total:
            errors.append(f"Total de transacciones distinto en {code}")
        if int(frame["fraudes"].sum()) != frauds:
            errors.append(f"Total de fraudes distinto en {code}")
        calculated = frame["fraudes"] / frame["transacciones"] * 100
        if ((calculated - frame["tasa_fraude_pct"]).abs() > 0.00011).any():
            errors.append(f"Tasas de fraude distintas en {code}")
    return errors


def as_view(data: pd.DataFrame, dimension: str, labels: dict | None = None) -> pd.DataFrame:
    result = data.copy()
    result[dimension] = result[dimension].astype(str)
    if labels:
        result[dimension] = result[dimension].map(labels).fillna(result[dimension])
    return result


def download_csv(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8-sig")
