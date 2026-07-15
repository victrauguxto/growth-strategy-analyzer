from utils.csv_reader import (
    load_and_process_dataset,
    extract_kpis,
)

from utils.html_generator import (
    generate_html_report,
)

from utils.sheets_client import (
    persist_test_result,
)

from dotenv import load_dotenv
from pathlib import Path


load_dotenv()


input_path = Path("input")
reports_path = Path("output")


if __name__ == "__main__":
    reports_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    files = [
        file_path
        for file_path in input_path.glob("dataset*.csv")
        if not file_path.stem.endswith("_processed")
    ]

    if not files:
        print(
            f"No CSV files found in: {input_path}"
        )

    processed_count = 0

    for file_path in files:
        print("-" * 80)
        print(
            f"Processing arquivo: {file_path.name}"
        )

        df, inicio, fim = (
            load_and_process_dataset(
                file_path
            )
        )

        kpis = extract_kpis(
            df
        )

        filename_no_extension = (
            file_path.stem
        )

        parceiro = (
            filename_no_extension
            .split("_", 2)[-1]
            .upper()
        )
        if not parceiro:
            parceiro = input(
                "Por favor, informe o nome do parceiro: "
            )

        recommendation, quantidade_grupos = (
            generate_html_report(
                kpis=kpis,
                parceiro=parceiro,
                periodo_inicio=inicio.strftime(
                    "%d/%m/%Y"
                ),
                periodo_fim=fim.strftime(
                    "%d/%m/%Y"
                ),
                output_path=(
                    reports_path
                    / (
                        f"{filename_no_extension}"
                        "_report.html"
                    )
                ),
            )
        )

        resumo = (
            f"Foram analisadas "
            f"{quantidade_grupos} variantes "
            f"de incentivo para o parceiro "
            f"{parceiro}. "
            "A comparação considera o "
            "percentual de cashback, o volume "
            "de compradores, o valor líquido "
            "total e o valor líquido gerado "
            "por comprador."
        )

        persist_test_result(
            test_name=filename_no_extension,
            description=resumo,
            recommendation=recommendation,
        )

        processed_count += 1

    print("-" * 80)
    print(
        f"Processamento finalizado. "
        f"{processed_count} arquivo(s) processado(s)."
    )