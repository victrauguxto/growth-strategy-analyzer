from utils.csv_reader import (
    load_and_process_dataset,
    extract_kpis,
)

from utils.html_generator import (
    generate_html_report,
)


file_path = "data/dataset_02_parceiroB.csv"


if __name__ == "__main__":

    df = load_and_process_dataset(
        file_path
    )

    kpis = extract_kpis(
        df
    )

    generate_html_report(
        kpis=kpis,
        parceiro="Parceiro A",
        periodo_inicio="01/01/2024",
        periodo_fim="31/01/2024",
        output_path=(
            "reports/"
            "parceiro_a_report.html"
        ),
    )