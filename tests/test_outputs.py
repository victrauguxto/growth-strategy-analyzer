"""Output-adapter tests for HTML and local/Sheets-compatible rows."""

import contextlib
import csv
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from utils.decision_engine import analyze_growth_tradeoff
from utils.html_generator import generate_html_report
import utils.sheets_client as sheets_client

from test_decision_engine import metrics


class OutputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.kpis = {
            "Grupo 1": metrics(4.0, 100, 100),
            "Grupo 2": metrics(5.0, 115, 95),
        }
        self.decision = analyze_growth_tradeoff(self.kpis)

    def test_html_exposes_decision_tradeoff_and_file_uri(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "report.html"
            terminal = io.StringIO()
            with contextlib.redirect_stdout(terminal):
                decision, count = generate_html_report(
                    self.kpis,
                    parceiro="Parceiro Teste",
                    output_path=report_path,
                    decision_result=self.decision,
                )

            html = report_path.read_text(encoding="utf-8")
            self.assertEqual(decision["decision_type"], "balanced_growth")
            self.assertEqual(count, 2)
            self.assertIn("Growth vs Resultado Econômico", html)
            self.assertIn("Escalar Grupo 2", html)
            self.assertIn("Growth equilibrado", html)
            self.assertIn("não contém usuários expostos", html)
            self.assertIn(report_path.resolve().as_uri(), terminal.getvalue())

    def test_sheet_row_uses_structured_decision(self) -> None:
        row = sheets_client.format_test_result(
            "dataset_01",
            "Duas variantes analisadas.",
            self.decision,
        )

        self.assertEqual(row[3], self.decision["summary"])
        self.assertEqual(
            row[4],
            "Escalar Grupo 2 — Growth equilibrado",
        )

    def test_local_csv_accumulates_results_with_one_header(self) -> None:
        first = sheets_client.format_test_result(
            "dataset_01", "Descrição 1", self.decision
        )
        second = sheets_client.format_test_result(
            "dataset_02", "Descrição 2", self.decision
        )

        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            history_path = directory_path / "test_results.csv"
            with (
                patch.object(
                    sheets_client,
                    "CSV_FALLBACK_DIR",
                    directory_path,
                ),
                patch.object(
                    sheets_client,
                    "CSV_RESULTS_PATH",
                    history_path,
                ),
            ):
                sheets_client.save_result_to_csv(first)
                sheets_client.save_result_to_csv(second)

            with history_path.open(
                encoding="utf-8-sig", newline=""
            ) as csv_file:
                rows = list(csv.reader(csv_file))

        self.assertEqual(rows, [sheets_client.CSV_HEADERS, first, second])


if __name__ == "__main__":
    unittest.main()
