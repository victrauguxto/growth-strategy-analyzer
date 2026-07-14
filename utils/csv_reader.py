import pandas
import pandas
from importlib import resources
import pandas as pd
from pydantic import BaseModel, field_validator
from typing import List
from pathlib import Path
import json


class dataset(BaseModel):
    data: str
    grupos_de_usuarios: str
    parceiro: str
    compradores: int
    comissao: float
    cashback: float
    vendas_totais: float
    
## indicadores:
"""
Crescimento:  Vendas totais
Crescimento:  Compradores
Monetização:  Comissão
Custo do incentivo:  Cashback
Rentabilidade:  Comissão - Cashback
Rentabilidade:  Margem direta
Eficiência:  Resultado por comprador
Eficiência:  GMV incremental por cashback adicional
Confiança:  Consistência diária
Confiança:  Intervalo de confiança

"""

def read_csv(file_path: str) -> pd.DataFrame:
    """Read a CSV file and return a Pandas DataFrame."""
    return pd.read_csv(file_path)


def load_and_process_dataset(file_path: str) -> pd.DataFrame:
    """Load a CSV file and process it."""
    df = read_csv(file_path)
    colunas_a_renomear = {
        "Data" : "data",
        "Grupos de usuários": "grupos_de_usuarios",
        "Parceiro" : "parceiro",
        "compradores" : "compradores",
        "comissão" : "comissao",
        "cashback" : "cashback",
        "vendas totais" : "vendas_totais"
    }
    df.rename(columns=colunas_a_renomear, inplace=True)
    df["data"] = pd.to_datetime(df["data"])
    df["comissao"] = df["comissao"].str.replace("R$", "").str.replace(" ", "").str.replace(".", "").str.replace(",", ".").astype(float)
    df["cashback"] = df["cashback"].str.replace("R$", "").str.replace(" ", "").str.replace(".", "").str.replace(",", ".").astype(float)
    df["vendas_totais"] = df["vendas_totais"].str.replace("R$", "").str.replace(" ", "").str.replace(".", "").str.replace(",", ".").astype(float)
    df["ticket_medio"] = (df["vendas_totais"] / df["compradores"]).round(2)
    df["valor_liquido"] = df["comissao"] - df["cashback"]
    df["percentual_comissao"] = (df["comissao"] / df["vendas_totais"] * 100).round(2)
    df["percentual_cashback"] = (df["cashback"] / df["vendas_totais"] * 100).round(2)
    df["margem_direta"] = (df["valor_liquido"] / df["vendas_totais"] * 100).round(2)

    return df 

def create_analytical_df(df):
    analytical_df = df.copy()
    colunas_a_manter = ["grupos_de_usuarios", "percentual_cashback", "valor_liquido", "percentual_comissao", "compradores"]
    analytical_df = analytical_df[colunas_a_manter]
    analytical_df = analytical_df.groupby("grupos_de_usuarios").agg({"percentual_cashback": "mean", "valor_liquido": "sum", "percentual_comissao": "mean", "compradores": "sum"})
    
    return analytical_df  

def extract_kpis(df):
    kpis_por_grupo = {}

    for grupo, grupo_df in df.groupby("grupos_de_usuarios"):
        valor_liquido_total = float(grupo_df["valor_liquido"].sum())
        compradores_total = int(grupo_df["compradores"].sum())

        percentual_cashback_medio = round(
            float(grupo_df["percentual_cashback"].mean()),
            2,
        )


        valor_liquido_por_comprador = (
            round(valor_liquido_total / compradores_total, 2)
            if compradores_total > 0
            else 0.0
        )

        kpis_por_grupo[grupo] = {
            "percentual_cashback": percentual_cashback_medio,
            "compradores": compradores_total,
            "valor_liquido": round(valor_liquido_total, 2),
            "valor_liquido_por_comprador": valor_liquido_por_comprador,
        }

    return kpis_por_grupo



def process_all_datasets(
    input_folder: str = "data",
    output_folder: str = "data/processed",
) -> None:
    input_path = Path(input_folder)
    output_path = Path(output_folder)

    output_path.mkdir(parents=True, exist_ok=True)

    files = [
        file_path
        for file_path in input_path.glob("dataset*.csv")
        if not file_path.stem.endswith("_processed")
    ]

    if not files:
        print(f"No CSV files found in: {input_path}")
        return

    processed_count = 0

    for file_path in files:
        print("-" * 80)
        try:
            df = load_and_process_dataset(file_path)

            processed_file_path = (
                output_path / f"{file_path.stem}_processed.csv"
            )

            analytical_df = create_analytical_df(df)
            kpis = extract_kpis(df)


            processed_count += 1

            print(
                f"Processed: {file_path.name} "
                f"-> {processed_file_path}"
            )
            
            kpis_json = json.dumps(kpis, indent=4)
            output_kpi_path = output_path / f"{file_path.stem}_kpis.json"

            with open(output_kpi_path, "w", encoding="utf-8") as f:
                f.write(kpis_json)

            print(f"Saved KPIs to: {output_kpi_path}")


        except Exception as error:
            print(f"Error processing {file_path.name}: {error}")

    print(
        f"Finished. Successfully processed "
        f"{processed_count} of {len(files)} files."
    )


