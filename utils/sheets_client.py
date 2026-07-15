from pandas.io import clipboards
import os
import gspread
from gspread import Client, Spreadsheet
from gspread.exceptions import SpreadsheetNotFound
from datetime import datetime

from utils.html_generator import get_recommendation


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
            "A planilha não foi encontrada. Verifique se a variável GOOGLE_SHEETS_SPREADSHEET_URL está configurada corretamente."
        ) from exc


from datetime import datetime


def format_test_for_sheets(
    test_name: str,
    description: str,
    recommendation: dict,
) -> list:
    return [
        test_name,
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        description,
        recommendation["justificativa"],
        f"Recomenda-se utilizar o {recommendation['grupo']}.",
    ]

test_result = {
    "test_name": "0001",
    "description": "Resumo executivo do teste.",
    "result": "Justificativa da recomendação.",
    "decision": "Escalar Grupo 2",
}

def write_test_results(
    spreadsheet: Spreadsheet,
    test_name: str,
    description: str,
    recommendation: dict,
) -> None:
    worksheet = spreadsheet.sheet1

    data_to_write = format_test_for_sheets(
        test_name,
        description,
        recommendation,
    )

    worksheet.append_row(
        data_to_write,
        value_input_option="USER_ENTERED",
    )


def persist_test_result(test_result: dict) -> None:
    csv_path = save_result_to_csv(test_result)

    if not is_sheets_configured():
        print(
            f"Google Sheets não configurado. "
            f"Resultado mantido em: {csv_path}"
        )
        return

    try:
        send_result_to_sheets(test_result)
        delete_local_csv(csv_path)

    except Exception as error:
        print(
            "Falha ao enviar para o Google Sheets. "
            "O CSV local foi mantido."
        )

        print(error)