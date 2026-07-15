import csv
import os
from datetime import datetime
from pathlib import Path

import gspread
from gspread import Client, Spreadsheet
from gspread.exceptions import SpreadsheetNotFound


CSV_FALLBACK_DIR = Path("data/test_results")
CSV_RESULTS_PATH = CSV_FALLBACK_DIR / "test_results.csv"

CSV_HEADERS = [
    "Nome do teste",
    "Data / Hora Execução",
    "Descrição",
    "Resultado",
    "Decisão tomada",
]


def get_google_client() -> Client:
    credentials_path = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS"
    )

    if not credentials_path:
        raise ValueError(
            "A variável GOOGLE_APPLICATION_CREDENTIALS "
            "não foi configurada."
        )

    return gspread.service_account(
        filename=credentials_path
    )


def get_spreadsheet() -> Spreadsheet:
    client = get_google_client()

    spreadsheet_url = os.getenv(
        "GOOGLE_SHEETS_SPREADSHEET_URL"
    )

    if not spreadsheet_url:
        raise ValueError(
            "A variável GOOGLE_SHEETS_SPREADSHEET_URL "
            "não foi configurada."
        )

    try:
        return client.open_by_url(
            spreadsheet_url
        )

    except SpreadsheetNotFound as exc:
        raise SpreadsheetNotFound(
            "A planilha não foi encontrada. "
            "Verifique se a variável "
            "GOOGLE_SHEETS_SPREADSHEET_URL "
            "está configurada corretamente e se a "
            "Service Account possui acesso à planilha."
        ) from exc


def format_test_result(
    test_name: str,
    description: str,
    recommendation: dict,
) -> list[str]:
    return [
        test_name,
        datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        ),
        description,
        recommendation["justificativa"],
        (
            "Recomenda-se utilizar o "
            f"{recommendation['grupo']}."
        ),
    ]


def write_test_results(
    spreadsheet: Spreadsheet,
    test_result: list[str],
) -> None:
    worksheet = spreadsheet.sheet1

    worksheet.append_row(
        test_result,
        value_input_option="USER_ENTERED",
    )


def save_result_to_csv(
    test_result: list[str],
) -> Path:
    CSV_FALLBACK_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    should_write_header = (
        not CSV_RESULTS_PATH.exists()
        or CSV_RESULTS_PATH.stat().st_size == 0
    )

    with CSV_RESULTS_PATH.open(
        mode="a",
        newline="",
        encoding="utf-8-sig",
    ) as csv_file:
        writer = csv.writer(csv_file)

        if should_write_header:
            writer.writerow(CSV_HEADERS)

        writer.writerow(test_result)

    return CSV_RESULTS_PATH


def is_sheets_configured() -> bool:
    return bool(
        os.getenv(
            "GOOGLE_APPLICATION_CREDENTIALS"
        )
        and os.getenv(
            "GOOGLE_SHEETS_SPREADSHEET_URL"
        )
    )


def send_result_to_sheets(
    test_result: list[str],
) -> None:
    spreadsheet = get_spreadsheet()

    write_test_results(
        spreadsheet=spreadsheet,
        test_result=test_result,
    )


def persist_test_result(
    test_name: str,
    description: str,
    recommendation: dict,
) -> None:
    test_result = format_test_result(
        test_name=test_name,
        description=description,
        recommendation=recommendation,
    )

    # Mantém um histórico local de todas as execuções,
    # independentemente da integração com o Google Sheets.
    csv_path = save_result_to_csv(
        test_result
    )

    if not is_sheets_configured():
        print(
            "Google Sheets não configurado. "
            f"Resultado mantido em: {csv_path}"
        )
        return

    try:
        send_result_to_sheets(
            test_result
        )

        print(
            "Resultado mantido no histórico local "
            f"em: {csv_path}"
        )

        print(
            "Resultado também enviado ao Google "
            "Sheets com sucesso."
        )

    except Exception as error:
        print(
            "Falha ao enviar para o Google Sheets. "
            f"O histórico local foi mantido em: {csv_path}"
        )

        print(
            f"Erro: {error}"
        )
