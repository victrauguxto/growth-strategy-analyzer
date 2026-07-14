from datetime import datetime
from pathlib import Path
from utils.graph_builder import graph_builder



def format_data(kpis: dict) -> dict:
    formatted_data = {}

    for grupo, metrics in kpis.items():
        formatted_data[grupo] = {
            "percentual_cashback": metrics["percentual_cashback"],
            "compradores": metrics["compradores"],
            "valor_liquido": metrics["valor_liquido"],
            "valor_liquido_por_comprador": metrics[
                "valor_liquido_por_comprador"
            ],
        }

    return formatted_data


def format_currency(value: float) -> str:
    formatted = f"{value:,.2f}"

    formatted = (
        formatted
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    return f"R$ {formatted}"


def format_number(value: int) -> str:
    #Formata no padrão Brasileiro
    return f"{value:,}".replace(",", ".")


def get_recommendation(kpis: dict) -> dict:
    
    #Seleciona o grupo com maior valor líquido total.

    recommended_group = max(
        kpis,
        key=lambda grupo: kpis[grupo]["valor_liquido"]
    )

    metrics = kpis[recommended_group]

    highest_value_per_buyer = max(
        item["valor_liquido_por_comprador"]
        for item in kpis.values()
    )

    reasons = [
        "apresentou o maior valor líquido total entre as variantes"
    ]

    if (
        metrics["valor_liquido_por_comprador"]
        == highest_value_per_buyer
    ):
        reasons.append(
            "também apresentou o maior valor líquido por comprador"
        )

    return {
        "grupo": recommended_group,
        "justificativa": (
            f"O {recommended_group} "
            + " e ".join(reasons)
            + "."
        ),
    }


def get_group_observation(
    grupo: str,
    metrics: dict,
    kpis: dict
) -> str:
    #Gera uma observação determinística simples para cada grupo.

    lowest_cashback = min(
        item["percentual_cashback"]
        for item in kpis.values()
    )

    highest_cashback = max(
        item["percentual_cashback"]
        for item in kpis.values()
    )

    highest_net_value = max(
        item["valor_liquido"]
        for item in kpis.values()
    )

    highest_buyers = max(
        item["compradores"]
        for item in kpis.values()
    )

    observations = []

    if metrics["percentual_cashback"] == lowest_cashback:
        observations.append("menor percentual de cashback")

    if metrics["percentual_cashback"] == highest_cashback:
        observations.append("maior percentual de cashback")

    if metrics["valor_liquido"] == highest_net_value:
        observations.append("maior resultado líquido")

    if metrics["compradores"] == highest_buyers:
        observations.append("maior volume de compradores")

    if not observations:
        return "Desempenho intermediário entre as variantes analisadas."

    return (
        observations[0].capitalize()
        + (
            ", " + ", ".join(observations[1:])
            if len(observations) > 1
            else ""
        )
        + "."
    )


def generate_html_report(
    kpis: dict,
    parceiro: str = "Parceiro não informado",
    periodo_inicio: str = "Não informado",
    periodo_fim: str = "Não informado",
    output_path: str = "reports/report.html",
) -> None:

    formatted_kpis = format_data(kpis)

    recommendation = get_recommendation(formatted_kpis)

    comparison_chart = graph_builder(
        kpis=formatted_kpis,
        recommended_group=(
            recommendation["grupo"]
        ),
    )

    generated_at = datetime.now().strftime(
        "%d/%m/%Y às %H:%M"
    )

    quantidade_grupos = len(formatted_kpis)

    # ==========================
    # TABELA COMPARATIVA
    # ==========================

    table_rows = ""

    for grupo, metrics in formatted_kpis.items():
        is_winner = (
            grupo == recommendation["grupo"]
        )

        row_class = (
            'class="winner-row"'
            if is_winner
            else ""
        )

        winner_badge = (
            '<span class="badge">Recomendado</span>'
            if is_winner
            else ""
        )

        table_rows += f"""
        <tr {row_class}>
            <td>
                <strong>{grupo}</strong>
                {winner_badge}
            </td>

            <td>
                {metrics["percentual_cashback"]:.2f}%
            </td>

            <td>
                {format_number(metrics["compradores"])}
            </td>

            <td>
                {format_currency(metrics["valor_liquido"])}
            </td>

            <td>
                {
                    format_currency(
                        metrics[
                            "valor_liquido_por_comprador"
                        ]
                    )
                }
            </td>
        </tr>
        """

    # ==========================
    # CARDS DOS GRUPOS
    # ==========================

    grupos_html = ""

    for grupo, metrics in formatted_kpis.items():

        observation = get_group_observation(
            grupo,
            metrics,
            formatted_kpis,
        )

        winner_class = (
            "card winner-card"
            if grupo == recommendation["grupo"]
            else "card"
        )

        winner_label = (
            '<div class="winner-label">'
            'Variante recomendada'
            '</div>'
            if grupo == recommendation["grupo"]
            else ""
        )

        grupos_html += f"""
        <article class="{winner_class}">

            {winner_label}

            <h3>{grupo}</h3>

            <div class="metrics-grid">

                <div class="metric-box">
                    <span class="metric-label">
                        Cashback
                    </span>

                    <span class="metric-value">
                        {
                            metrics[
                                "percentual_cashback"
                            ]
                        :.2f}%
                    </span>
                </div>


                <div class="metric-box">
                    <span class="metric-label">
                        Compradores
                    </span>

                    <span class="metric-value">
                        {
                            format_number(
                                metrics["compradores"]
                            )
                        }
                    </span>
                </div>


                <div class="metric-box">
                    <span class="metric-label">
                        Valor Líquido
                    </span>

                    <span class="metric-value">
                        {
                            format_currency(
                                metrics["valor_liquido"]
                            )
                        }
                    </span>
                </div>


                <div class="metric-box">
                    <span class="metric-label">
                        Valor Líquido / Comprador
                    </span>

                    <span class="metric-value">
                        {
                            format_currency(
                                metrics[
                                    "valor_liquido_por_comprador"
                                ]
                            )
                        }
                    </span>
                </div>

            </div>

            <p class="observation">
                {observation}
            </p>

        </article>
        """

    # ==========================
    # HTML FINAL
    # ==========================

    html = f"""
    <!DOCTYPE html>

    <html lang="pt-br">

    <head>
        
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

        <meta charset="UTF-8">

        <meta
            name="viewport"
            content="width=device-width, initial-scale=1.0"
        >

        <title>
            Análise de Teste A/B - {parceiro}
        </title>


        <style>

            * {{
                box-sizing: border-box;
            }}


            body {{
                margin: 0;

                font-family:
                    Arial,
                    Helvetica,
                    sans-serif;

                background:
                    #f4f6f8;

                color:
                    #1f2937;
            }}


            .container {{
                max-width: 1100px;

                margin: 0 auto;

                padding:
                    40px
                    24px
                    80px;
            }}


            .report-header {{
                margin-bottom: 32px;
            }}


            .report-header h1 {{
                margin-bottom: 8px;

                font-size: 32px;

                color:
                    #111827;
            }}


            .subtitle {{
                color:
                    #6b7280;

                font-size:
                    16px;
            }}


            .report-info {{
                display: grid;

                grid-template-columns:
                    repeat(
                        auto-fit,
                        minmax(180px, 1fr)
                    );

                gap: 16px;

                margin-top: 24px;
            }}


            .info-item {{
                background:
                    white;

                padding: 16px;

                border-radius: 10px;

                border:
                    1px solid #e5e7eb;
            }}


            .info-label {{
                display: block;

                margin-bottom: 6px;

                color:
                    #6b7280;

                font-size:
                    13px;
            }}


            .info-value {{
                font-weight: bold;

                color:
                    #111827;
            }}


            section {{
                margin-bottom: 32px;
            }}


            .section-box {{
                background:
                    white;

                padding: 28px;

                border-radius: 12px;

                box-shadow:
                    0 2px 8px
                    rgba(0, 0, 0, 0.05);
            }}


            .highlight {{
                background:
                    #ecfdf3;

                border-left:
                    6px solid #16a34a;
            }}


            .highlight h2 {{
                margin-top: 0;

                color:
                    #166534;
            }}


            .recommendation {{
                margin:
                    12px
                    0;

                font-size:
                    28px;

                font-weight:
                    bold;

                color:
                    #14532d;
            }}


            h2 {{
                margin-top: 0;

                color:
                    #111827;
            }}


            .table-container {{
                overflow-x: auto;
            }}


            table {{
                width: 100%;

                border-collapse:
                    collapse;

                margin-top:
                    20px;
            }}


            th {{
                padding:
                    14px;

                text-align:
                    left;

                background:
                    #f3f4f6;

                color:
                    #374151;

                font-size:
                    14px;
            }}


            td {{
                padding:
                    16px
                    14px;

                border-bottom:
                    1px solid #e5e7eb;
            }}


            tbody tr:nth-child(even) {{
                background:
                    #fafafa;
            }}


            .winner-row {{
                background:
                    #f0fdf4
                    !important;
            }}


            .badge {{
                display:
                    inline-block;

                margin-left:
                    8px;

                padding:
                    4px
                    8px;

                border-radius:
                    999px;

                background:
                    #dcfce7;

                color:
                    #166534;

                font-size:
                    11px;

                font-weight:
                    bold;
            }}


            .cards-grid {{
                display:
                    grid;

                grid-template-columns:
                    repeat(
                        auto-fit,
                        minmax(280px, 1fr)
                    );

                gap:
                    20px;
            }}


            .card {{
                position:
                    relative;

                background:
                    white;

                padding:
                    24px;

                border-radius:
                    12px;

                border:
                    1px solid #e5e7eb;

                box-shadow:
                    0 2px 8px
                    rgba(0, 0, 0, 0.05);
            }}


            .winner-card {{
                border:
                    2px solid #22c55e;
            }}


            .winner-label {{
                position:
                    absolute;

                top:
                    -12px;

                right:
                    16px;

                padding:
                    6px
                    12px;

                border-radius:
                    999px;

                background:
                    #16a34a;

                color:
                    white;

                font-size:
                    12px;

                font-weight:
                    bold;
            }}


            .card h3 {{
                margin-top:
                    4px;

                font-size:
                    22px;
            }}


            .metrics-grid {{
                display:
                    grid;

                grid-template-columns:
                    repeat(2, 1fr);

                gap:
                    16px;

                margin-top:
                    20px;
            }}


            .metric-box {{
                padding:
                    14px;

                background:
                    #f9fafb;

                border-radius:
                    8px;
            }}


            .metric-label {{
                display:
                    block;

                margin-bottom:
                    6px;

                color:
                    #6b7280;

                font-size:
                    12px;
            }}


            .metric-value {{
                font-size:
                    18px;

                font-weight:
                    bold;

                color:
                    #111827;
            }}


            .observation {{
                margin-top:
                    20px;

                padding-top:
                    16px;

                border-top:
                    1px solid #e5e7eb;

                color:
                    #4b5563;
            }}


            .placeholder {{
                padding:
                    50px
                    20px;

                border:
                    2px dashed #d1d5db;

                border-radius:
                    10px;

                text-align:
                    center;

                color:
                    #6b7280;

                background:
                    #f9fafb;
            }}


            .footer {{
                margin-top:
                    48px;

                padding-top:
                    24px;

                border-top:
                    1px solid #d1d5db;

                color:
                    #6b7280;

                font-size:
                    13px;

                text-align:
                    center;
            }}


            @media (
                max-width: 600px
            ) {{

                .container {{
                    padding:
                        24px
                        16px
                        50px;
                }}


                .report-header h1 {{
                    font-size:
                        26px;
                }}


                .metrics-grid {{
                    grid-template-columns:
                        1fr;
                }}


                .recommendation {{
                    font-size:
                        22px;
                }}

            }}
            .chart-section {{
                background: #ffffff;
                padding: 32px;
                margin-bottom: 24px;
                border-radius: 16px;
                box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06);
            }}

            .chart-header {{
                text-align: center;
                margin-bottom: 24px;
            }}

            .chart-header h2 {{
                margin: 0 0 12px;
                color: #0f172a;
            }}

            .chart-header p {{
                margin: 0;
                color: #64748b;
            }}

            .chart-container {{
                position: relative;
                height: 420px;
            }}

            .chart-note {{
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 6px;
                margin-top: 20px;
                color: #475569;
                font-size: 14px;
            }}

            .winner-indicator {{
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background: #16a34a;
            }}

        </style>

    </head>


    <body>

        <main class="container">


            <!-- CABEÇALHO -->

            <header class="report-header">

                <h1>
                    Análise de Teste A/B
                </h1>

                <p class="subtitle">
                    Comparação de performance entre
                    variantes de cashback
                </p>


                <div class="report-info">

                    <div class="info-item">

                        <span class="info-label">
                            Parceiro
                        </span>

                        <span class="info-value">
                            {parceiro}
                        </span>

                    </div>


                    <div class="info-item">

                        <span class="info-label">
                            Período analisado
                        </span>

                        <span class="info-value">
                            {periodo_inicio}
                            a
                            {periodo_fim}
                        </span>

                    </div>


                    <div class="info-item">

                        <span class="info-label">
                            Variantes analisadas
                        </span>

                        <span class="info-value">
                            {quantidade_grupos}
                        </span>

                    </div>


                    <div class="info-item">

                        <span class="info-label">
                            Relatório gerado em
                        </span>

                        <span class="info-value">
                            {generated_at}
                        </span>

                    </div>

                </div>

            </header>


            <!-- RESUMO EXECUTIVO -->

            <section class="section-box">

                <h2>
                    Resumo Executivo
                </h2>

                <p>
                    Foram analisadas
                    <strong>
                        {quantidade_grupos}
                        variantes
                    </strong>
                    de incentivo para o parceiro
                    <strong>{parceiro}</strong>.

                    A comparação considera
                    o percentual de cashback,
                    o volume de compradores,
                    o valor líquido total
                    e o valor líquido gerado
                    por comprador.
                </p>

            </section>


            <!-- RECOMENDAÇÃO -->

            <section
                class="
                    section-box
                    highlight
                "
            >

                <h2>
                    Recomendação
                </h2>

                <p class="recommendation">
                    Escalar
                    {recommendation["grupo"]}
                </p>

                <p>
                    <strong>
                        Justificativa:
                    </strong>

                    {
                        recommendation[
                            "justificativa"
                        ]
                    }
                </p>

            </section>


            <!-- TABELA -->

            <section class="section-box">

                <h2>
                    Comparação das Variantes
                </h2>

                <p>
                    Visão consolidada dos
                    principais indicadores
                    observados durante o teste.
                </p>


                <div class="table-container">

                    <table>

                        <thead>

                            <tr>

                                <th>
                                    Grupo
                                </th>

                                <th>
                                    Cashback
                                </th>

                                <th>
                                    Compradores
                                </th>

                                <th>
                                    Valor Líquido
                                </th>

                                <th>
                                    Líquido /
                                    Comprador
                                </th>

                            </tr>

                        </thead>


                        <tbody>

                            {table_rows}

                        </tbody>

                    </table>

                </div>

            </section>


            <!-- VISUALIZAÇÕES -->

            <section class="section-box">

                <h2>
                    Visualizações
                </h2>

                <div class="placeholder">


                            {comparison_chart}

                        
                    

                </div>

            </section>


            <!-- DETALHAMENTO -->

            <section>

                <h2>
                    Detalhamento por Grupo
                </h2>

                <div class="cards-grid">

                    {grupos_html}

                </div>

            </section>


            <!-- CONCLUSÃO -->

            <section class="section-box">

                <h2>
                    Conclusão
                </h2>

                <p>
                    Com base nos resultados
                    observados,
                    <strong>
                        {recommendation["grupo"]}
                    </strong>
                    apresentou o melhor resultado
                    dentro do critério atual
                    de decisão.
                </p>

                <p>
                    Esta recomendação representa
                    uma comparação dos resultados
                    observados no teste e não deve
                    ser interpretada automaticamente
                    como uma projeção linear para
                    100% do tráfego.
                </p>

            </section>


            <footer class="footer">

                Growth Strategy Analyzer

                <br>

                Relatório gerado automaticamente
                em {generated_at}

            </footer>


        </main>

    </body>

    </html>
    """

    output_file = Path(output_path)

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file.write_text(
        html,
        encoding="utf-8",
    )

    print(
        f"Relatório gerado em: "
        f"{output_file.resolve()}"
    )