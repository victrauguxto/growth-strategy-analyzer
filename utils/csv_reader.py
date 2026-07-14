from importlib import resources
import pandas as pd
from pydantic import BaseModel, field_validator
from typing import List
from pathlib import Path


class dataset(BaseModel):
    data: str
    grupos_de_usuarios: str
    parceiro: str
    compradores: int
    comissao: float
    cashback: float
    vendas_totais: float
    


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
    
    custo_por_comprador =(max(df["cashback"]) - min(df["cashback"])) / (max(df["compradores"]) - min(df["compradores"]))  

    print(f"custo por comprador: {custo_por_comprador}")
    return df   


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
        try:
            df = load_and_process_dataset(file_path)

            processed_file_path = (
                output_path / f"{file_path.stem}_processed.csv"
            )

            df.to_csv(processed_file_path, index=False)

            processed_count += 1

            print(
                f"Processed: {file_path.name} "
                f"-> {processed_file_path}"
            )

        except Exception as error:
            print(f"Error processing {file_path.name}: {error}")

    print(
        f"Finished. Successfully processed "
        f"{processed_count} of {len(files)} files."
    )