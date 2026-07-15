"""CSV loading, normalization, and KPI aggregation."""

from datetime import date
from pathlib import Path

import pandas as pd


EXPECTED_COLUMNS = {
    "Data",
    "Grupos de usuários",
    "Parceiro",
    "compradores",
    "comissão",
    "cashback",
    "vendas totais",
}

COLUMN_NAMES = {
    "Data": "data",
    "Grupos de usuários": "grupos_de_usuarios",
    "Parceiro": "parceiro",
    "compradores": "compradores",
    "comissão": "comissao",
    "cashback": "cashback",
    "vendas totais": "vendas_totais",
}


def read_csv(file_path: str | Path) -> pd.DataFrame:
    """Read a UTF-8 CSV file into a DataFrame."""
    return pd.read_csv(file_path)


def _parse_currency(series: pd.Series) -> pd.Series:
    """Convert Brazilian currency strings or numeric values to floats."""
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="raise").astype(float)

    normalized = (
        series.astype("string")
        .str.replace("R$", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    return pd.to_numeric(normalized, errors="raise").astype(float)


def _safe_ratio(numerator: float, denominator: float) -> float:
    """Return a percentage ratio, avoiding division by zero."""
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def load_and_process_dataset(
    file_path: str | Path,
) -> tuple[pd.DataFrame, date, date]:
    """Load and normalize one cashback A/B test dataset."""
    df = read_csv(file_path)

    missing_columns = EXPECTED_COLUMNS.difference(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Colunas obrigatórias ausentes: {missing}")

    if df.empty:
        raise ValueError("O dataset está vazio.")

    df = df.rename(columns=COLUMN_NAMES).copy()
    df["data"] = pd.to_datetime(df["data"], errors="raise")
    df["compradores"] = pd.to_numeric(
        df["compradores"], errors="raise"
    ).astype(int)

    for column in ("comissao", "cashback", "vendas_totais"):
        df[column] = _parse_currency(df[column])

    df["ticket_medio"] = (
        df["vendas_totais"]
        .div(df["compradores"].replace(0, pd.NA))
        .fillna(0.0)
        .round(2)
    )
    df["valor_liquido"] = df["comissao"] - df["cashback"]
    df["percentual_comissao"] = (
        df["comissao"]
        .div(df["vendas_totais"].replace(0, pd.NA))
        .mul(100)
        .fillna(0.0)
        .round(2)
    )
    df["percentual_cashback"] = (
        df["cashback"]
        .div(df["vendas_totais"].replace(0, pd.NA))
        .mul(100)
        .fillna(0.0)
        .round(2)
    )
    df["margem_direta"] = (
        df["valor_liquido"]
        .div(df["vendas_totais"].replace(0, pd.NA))
        .mul(100)
        .fillna(0.0)
        .round(2)
    )

    inicio = df["data"].min().date()
    fim = df["data"].max().date()
    return df, inicio, fim


def extract_kpis(df: pd.DataFrame) -> dict[str, dict[str, float | int]]:
    """Aggregate deterministic KPIs for every variant in one test."""
    kpis_por_grupo: dict[str, dict[str, float | int]] = {}

    for grupo, grupo_df in df.groupby("grupos_de_usuarios"):
        compradores = int(grupo_df["compradores"].sum())
        vendas = float(grupo_df["vendas_totais"].sum())
        comissao = float(grupo_df["comissao"].sum())
        cashback = float(grupo_df["cashback"].sum())
        valor_liquido = comissao - cashback

        kpis_por_grupo[str(grupo)] = {
            "percentual_cashback": _safe_ratio(cashback, vendas),
            "percentual_comissao": _safe_ratio(comissao, vendas),
            "compradores": compradores,
            "vendas_totais": round(vendas, 2),
            "comissao": round(comissao, 2),
            "cashback": round(cashback, 2),
            "valor_liquido": round(valor_liquido, 2),
            "valor_liquido_por_comprador": round(
                valor_liquido / compradores, 2
            ) if compradores > 0 else 0.0,
            "vendas_por_comprador": round(
                vendas / compradores, 2
            ) if compradores > 0 else 0.0,
        }

    return kpis_por_grupo


def create_analytical_df(df: pd.DataFrame) -> pd.DataFrame:
    """Return the consolidated KPI table kept for API compatibility."""
    return pd.DataFrame.from_dict(extract_kpis(df), orient="index")


def process_all_datasets() -> None:
    """Legacy helper that saves KPI JSON files for all input datasets."""
    import json

    input_path = Path("input")
    output_path = Path("output")
    output_path.mkdir(parents=True, exist_ok=True)

    files = sorted(
        file_path
        for file_path in input_path.glob("dataset*.csv")
        if not file_path.stem.endswith("_processed")
    )

    if not files:
        print(f"No CSV files found in: {input_path}")
        return

    processed_count = 0
    for file_path in files:
        try:
            df, _, _ = load_and_process_dataset(file_path)
            kpis = extract_kpis(df)
            output_kpi_path = output_path / f"{file_path.stem}_kpis.json"
            output_kpi_path.write_text(
                json.dumps(kpis, indent=4, ensure_ascii=False),
                encoding="utf-8",
            )
            processed_count += 1
            print(f"Saved KPIs to: {output_kpi_path}")
        except Exception as error:
            print(f"Error processing {file_path.name}: {error}")

    print(
        "Finished. Successfully processed "
        f"{processed_count} of {len(files)} files."
    )
