from utils.csv_reader import (
    load_and_process_dataset,
    extract_kpis,
    process_all_datasets
)

from utils.html_generator import (
    generate_html_report,
)

from utils.sheets_client import (
    get_google_client,
    write_test_results,
    get_spreadsheet
)

from dotenv import load_dotenv

from pathlib import Path


load_dotenv()


file_path = "data/dataset_02_parceiroB.csv"
input_path = Path("input")
reports_path = Path("output")


if __name__ == "__main__":
    reports_path.mkdir(parents=True, exist_ok=True)
    files = [
        file_path
        for file_path in input_path.glob("dataset*.csv")
        if not file_path.stem.endswith("_processed")
    ]

    

    if not files:
        print(f"No CSV files found in: {input_path}")


    processed_count = 0

    for file_path in files:
        print("-" * 80)
        print(f"Processing arquivo: {file_path.name}")

        df, inicio, fim = load_and_process_dataset(
            file_path
        )
        filename = Path(file_path).name

        kpis = extract_kpis(
            df
        )

        filename_no_extension = Path(file_path).stem

        recommendation = generate_html_report(
            kpis=kpis,
            parceiro=filename_no_extension.split("_", 2)[-1].upper(),
            periodo_inicio=inicio.strftime("%d/%m/%Y"),
            periodo_fim=fim.strftime("%d/%m/%Y"),
            output_path=(
                reports_path/
                f"{filename_no_extension}_report.html"
            ),
        )


        spreadsheet = get_spreadsheet()

        write_test_results(
            spreadsheet=spreadsheet,
            test_name="Teste 0001",
            description="Resumo executivo do teste.",
            recommendation=recommendation,
        )
        print(
            "Google Sheets atualizado com sucesso:"
        )

        print(
            spreadsheet.url
        )