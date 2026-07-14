import json

def format_data(kpis: dict) -> dict:
    formatted_data = {}
    for grupo, metrics in kpis.items():
        formatted_data[grupo] = {
            "percentual_cashback": metrics["percentual_cashback"],
            "compradores": metrics["compradores"],
            "valor_liquido": metrics["valor_liquido"],
            "valor_liquido_por_comprador": metrics["valor_liquido_por_comprador"],
        }
    return grupo, formatted_data

def generate_html_report(kpis: dict) -> None:
    grupos_html = ""

    for grupo, metrics in kpis.items():
        total_liquido = metrics["valor_liquido"]
        media_liquida = metrics["valor_liquido_por_comprador"]
        compradores = metrics["compradores"]
        percentual_cashback = metrics["percentual_cashback"]

        grupos_html += f"""
        <section>
            <h2>{grupo}</h2>

            <p>
                <strong>Total Líquido:</strong>
                R$ {total_liquido:,.2f}
            </p>

            <p>
                <strong>Valor Líquido por Comprador:</strong>
                R$ {media_liquida:,.2f}
            </p>

            <p>
                <strong>Compradores:</strong>
                {compradores:,}
            </p>

            <p>
                <strong>Percentual de Cashback:</strong>
                {percentual_cashback:.2f}%
            </p>
        </section>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta
            name="viewport"
            content="width=device-width, initial-scale=1.0"
        >

        <title>Análise de Crescimento</title>

        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 900px;
                margin: 40px auto;
                padding: 0 20px;
                background-color: #f5f5f5;
            }}

            h1 {{
                text-align: center;
            }}

            section {{
                background-color: white;
                padding: 24px;
                margin-bottom: 20px;
                border-radius: 8px;
            }}

            h2 {{
                margin-top: 0;
            }}
        </style>
    </head>

    <body>
        <h1>Análise de Crescimento</h1>

        {grupos_html}
    </body>
    </html>
    """

    with open("report.html", "w", encoding="utf-8") as file:
        file.write(html)