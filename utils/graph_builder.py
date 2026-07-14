import json


def graph_builder(kpis: dict, recommended_group: str) -> str:
    """
    Gera o HTML/JavaScript de um gráfico de barras agrupadas usando Chart.js.

    Cada grupo é exibido no eixo X.
    Cada indicador é uma série de barras:
        - Compradores
        - Valor Líquido
        - Líquido por Comprador

    Os valores são normalizados de forma relativa:
    o maior valor de cada indicador recebe 100%.

    O grupo recomendado recebe destaque visual em verde.

    Args:
        kpis: Dicionário com os KPIs por grupo.
        recommended_group: Nome do grupo recomendado.

    Returns:
        String HTML contendo o canvas e o script do gráfico.
    """

    grupos = list(kpis.keys())

    indicadores = {
        "compradores": {
            "label": "Compradores",
            "color": "#2563eb",
        },
        "valor_liquido": {
            "label": "Valor Líquido",
            "color": "#f59e0b",
        },
        "valor_liquido_por_comprador": {
            "label": "Líquido por Comprador",
            "color": "#7c3aed",
        },
    }

    # ---------------------------------------------------------
    # Normalização
    # O melhor grupo de cada indicador recebe 100%.
    # ---------------------------------------------------------

    normalized_data = {}

    for indicador in indicadores:
        valores = [
            kpis[grupo][indicador]
            for grupo in grupos
        ]

        max_value = max(valores)

        if max_value == 0:
            normalized_data[indicador] = [0 for _ in valores]
        else:
            normalized_data[indicador] = [
                round((valor / max_value) * 100, 2)
                for valor in valores
            ]

    # ---------------------------------------------------------
    # Datasets do Chart.js
    # ---------------------------------------------------------

    datasets = []

    for indicador, config in indicadores.items():
        border_widths = [
            3 if grupo == recommended_group else 0
            for grupo in grupos
        ]

        border_colors = [
            "#16a34a" if grupo == recommended_group
            else config["color"]
            for grupo in grupos
        ]

        datasets.append({
            "label": config["label"],
            "data": normalized_data[indicador],
            "backgroundColor": config["color"],
            "borderColor": border_colors,
            "borderWidth": border_widths,
            "borderRadius": 6,
            "borderSkipped": False,
        })

    grupos_json = json.dumps(
        grupos,
        ensure_ascii=False
    )

    datasets_json = json.dumps(
        datasets,
        ensure_ascii=False
    )

    recommended_group_json = json.dumps(
        recommended_group,
        ensure_ascii=False
    )

    # Dados reais para mostrar no tooltip
    raw_data = {
        grupo: {
            "compradores": kpis[grupo]["compradores"],
            "valor_liquido": kpis[grupo]["valor_liquido"],
            "valor_liquido_por_comprador":
                kpis[grupo]["valor_liquido_por_comprador"],
        }
        for grupo in grupos
    }

    raw_data_json = json.dumps(
        raw_data,
        ensure_ascii=False
    )

    return f"""
    <section class="chart-section">

        <div class="chart-header">
            <h2>Comparação Visual</h2>

            <p>
                Comparação relativa dos principais indicadores entre
                as variantes. 
            </p>
        </div>

        <div class="chart-container">
            <canvas id="comparisonChart"></canvas>
        </div>

        <div class="chart-note">
            <span class="winner-indicator"></span>
            <strong>{recommended_group}</strong>
            é o grupo recomendado.
        </div>

    </section>

    <script>
        const grupos = {grupos_json};
        const recommendedGroup = {recommended_group_json};
        const rawData = {raw_data_json};

        const comparisonChart = new Chart(
            document.getElementById("comparisonChart"),
            {{
                type: "bar",

                data: {{
                    labels: grupos,
                    datasets: {datasets_json}
                }},

                options: {{
                    responsive: true,
                    maintainAspectRatio: false,

                    interaction: {{
                        mode: "index",
                        intersect: false
                    }},

                    plugins: {{

                        legend: {{
                            position: "top",

                            labels: {{
                                usePointStyle: true,
                                pointStyle: "rectRounded",
                                padding: 20,

                                font: {{
                                    size: 13
                                }}
                            }}
                        }},

                        tooltip: {{
                            callbacks: {{

                                title: function(context) {{
                                    const grupo = context[0].label;

                                    if (grupo === recommendedGroup) {{
                                        return grupo + " — Recomendado";
                                    }}

                                    return grupo;
                                }},

                                label: function(context) {{
                                    const grupo = context.label;
                                    const datasetLabel =
                                        context.dataset.label;

                                    let realValue;

                                    if (
                                        datasetLabel === "Compradores"
                                    ) {{
                                        realValue =
                                            rawData[grupo]
                                                .compradores
                                                .toLocaleString(
                                                    "pt-BR"
                                                );

                                        return (
                                            datasetLabel +
                                            ": " +
                                            realValue +
                                            " compradores" +
                                            " (" +
                                            context.raw +
                                            "% relativo)"
                                        );
                                    }}

                                    if (
                                        datasetLabel ===
                                        "Valor Líquido"
                                    ) {{
                                        realValue =
                                            rawData[grupo]
                                                .valor_liquido
                                                .toLocaleString(
                                                    "pt-BR",
                                                    {{
                                                        style: "currency",
                                                        currency: "BRL"
                                                    }}
                                                );

                                        return (
                                            datasetLabel +
                                            ": " +
                                            realValue +
                                            " (" +
                                            context.raw +
                                            "% relativo)"
                                        );
                                    }}

                                    if (
                                        datasetLabel ===
                                        "Líquido por Comprador"
                                    ) {{
                                        realValue =
                                            rawData[grupo]
                                                .valor_liquido_por_comprador
                                                .toLocaleString(
                                                    "pt-BR",
                                                    {{
                                                        style: "currency",
                                                        currency: "BRL"
                                                    }}
                                                );

                                        return (
                                            datasetLabel +
                                            ": " +
                                            realValue +
                                            " (" +
                                            context.raw +
                                            "% relativo)"
                                        );
                                    }}

                                    return datasetLabel;
                                }}
                            }}
                        }}
                    }},

                    scales: {{

                        x: {{
                            offset: true,

                            grid: {{
                                display: false
                            }},

                            ticks: {{
                                color: function(context) {{
                                    const grupo =
                                        grupos[context.index];

                                    return grupo === recommendedGroup
                                        ? "#16a34a"
                                        : "#475569";
                                }},

                                font: function(context) {{
                                    const grupo =
                                        grupos[context.index];

                                    return {{
                                        size: 13,
                                        weight:
                                            grupo === recommendedGroup
                                                ? "bold"
                                                : "normal"
                                    }};
                                }}
                            }}
                        }},

                        y: {{
                            beginAtZero: true,
                            suggestedMax: 110,

                            title: {{
                                display: true,
                                text: "Performance relativa"
                            }},

                            ticks: {{
                                callback: function(value) {{
                                    return value + "%";
                                }}
                            }},

                            grid: {{
                                color:
                                    "rgba(148, 163, 184, 0.18)"
                            }}
                        }}
                    }}
                }}
            }}
        );
    </script>
    """