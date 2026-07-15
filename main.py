"""Command-line entry point for the Growth Strategy Analyzer."""

import argparse
from pathlib import Path
import webbrowser

from dotenv import load_dotenv

from utils.csv_reader import extract_kpis, load_and_process_dataset
from utils.decision_engine import analyze_growth_tradeoff
from utils.html_generator import generate_html_report
from utils.sheets_client import persist_test_result


INPUT_PATH = Path("input")
REPORTS_PATH = Path("output")
SEPARATOR = "-" * 80


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Analisa os testes A/B de cashback presentes em input/."
        )
    )
    parser.add_argument(
        "--open-report",
        action="store_true",
        help="Abre cada relatorio no navegador depois da geracao.",
    )
    return parser.parse_args()


def _format_change(value: float | None, suffix: str = "%") -> str:
    if value is None:
        return "N/D"
    return f"{value:+.2f}{suffix}"


def _print_decision_summary(file_name: str, decision: dict) -> None:
    recommended = decision.get("recommended_group")
    print(SEPARATOR)
    print(f"Processed: {file_name}")
    print()
    print(f"Recommendation: {recommended or 'Não disponível'}")
    print(f"Decision: {decision['decision_label']}")
    print(f"Confidence: {decision['confidence'].capitalize()}")

    if not recommended:
        print()
        print(decision["summary"])
        return

    tradeoff_group = decision.get("tradeoff_group") or recommended
    comparison = decision["comparisons"].get(tradeoff_group, {})
    print()
    print("Growth trade-off vs baseline:")
    if tradeoff_group != recommended:
        print(f"Evaluated variant: {tradeoff_group}")
    print(
        "Buyers: "
        f"{_format_change(comparison.get('buyer_uplift_pct'))}"
    )
    print(
        "Net value: "
        f"{_format_change(comparison.get('net_value_change_pct'))}"
    )
    print(
        "Effective cashback: "
        f"{_format_change(comparison.get('cashback_rate_increase_pp'), ' pp')}"
    )


def _partner_name(df, file_path: Path) -> str:
    partners = df["parceiro"].dropna().astype(str).unique()
    if len(partners):
        return partners[0]
    return file_path.stem.split("_", 2)[-1].upper()


def main() -> None:
    """Process every dataset and keep failures isolated per file."""
    load_dotenv()
    args = _parse_args()
    REPORTS_PATH.mkdir(parents=True, exist_ok=True)

    files = sorted(
        file_path
        for file_path in INPUT_PATH.glob("dataset*.csv")
        if not file_path.stem.endswith("_processed")
    )
    if not files:
        print(f"No CSV files found in: {INPUT_PATH}")
        return

    processed_count = 0
    for file_path in files:
        try:
            df, start_date, end_date = load_and_process_dataset(file_path)
            kpis = extract_kpis(df)
            decision = analyze_growth_tradeoff(kpis)
            partner = _partner_name(df, file_path)
            report_path = (
                REPORTS_PATH / f"{file_path.stem}_report.html"
            ).resolve()

            _print_decision_summary(file_path.name, decision)
            _, group_count = generate_html_report(
                kpis=kpis,
                parceiro=partner,
                periodo_inicio=start_date.strftime("%d/%m/%Y"),
                periodo_fim=end_date.strftime("%d/%m/%Y"),
                output_path=report_path,
                decision_result=decision,
            )

            description = (
                f"Foram analisadas {group_count} variantes de incentivo para "
                f"o parceiro {partner}. A variante baseline foi "
                f"{decision.get('baseline_variant') or 'não identificada'}."
            )
            persist_test_result(
                test_name=file_path.stem,
                description=description,
                recommendation=decision,
            )

            if args.open_report:
                webbrowser.open(report_path.as_uri())

            processed_count += 1
        except Exception as error:
            print(SEPARATOR)
            print(f"Falha ao processar {file_path.name}: {error}")

    print(SEPARATOR)
    print(
        "Processamento finalizado. "
        f"{processed_count} de {len(files)} arquivo(s) processado(s)."
    )


if __name__ == "__main__":
    main()
