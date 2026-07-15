"""Executive HTML report generation."""

from datetime import datetime
from html import escape
from pathlib import Path

from utils.decision_engine import analyze_growth_tradeoff
from utils.graph_builder import graph_builder


CONFIDENCE_LABELS = {
    "high": "Alta",
    "medium": "Média",
    "low": "Baixa",
}


def format_data(kpis: dict) -> dict:
    """Copy the KPI fields consumed by the report and chart."""
    fields = (
        "percentual_cashback",
        "percentual_comissao",
        "compradores",
        "vendas_totais",
        "comissao",
        "cashback",
        "valor_liquido",
        "valor_liquido_por_comprador",
        "vendas_por_comprador",
    )
    return {
        str(group): {
            field: metrics.get(field, 0)
            for field in fields
        }
        for group, metrics in kpis.items()
    }


def format_currency(value: float) -> str:
    """Format a number as Brazilian currency."""
    formatted = f"{float(value):,.2f}"
    formatted = (
        formatted.replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
    return f"R$ {formatted}"


def format_number(value: int | float) -> str:
    """Format an integer using Brazilian thousands separators."""
    return f"{int(value):,}".replace(",", ".")


def format_change(value: float | None, suffix: str = "%") -> str:
    """Format a signed comparison value or a safe unavailable marker."""
    if value is None:
        return "N/D"
    return f"{value:+.2f}{suffix}"


def get_recommendation(kpis: dict) -> dict:
    """Compatibility wrapper backed by the deterministic decision engine."""
    return analyze_growth_tradeoff(kpis)


def get_group_observation(
    group: str,
    metrics: dict,
    decision: dict,
) -> str:
    """Build a deterministic observation for one variant."""
    labels = []
    if group == decision.get("baseline_variant"):
        labels.append("variante baseline de menor cashback efetivo")
    if group == decision.get("economic_winner"):
        labels.append("maior valor líquido")
    if group == decision.get("growth_winner"):
        labels.append("maior volume de compradores")
    if group == decision.get("efficiency_winner"):
        labels.append("maior valor líquido por comprador")
    if not labels:
        return "Desempenho intermediário entre as variantes analisadas."
    return labels[0].capitalize() + ", " + ", ".join(labels[1:]) + "."


def _list_items(items: list[str]) -> str:
    return "".join(f"<li>{escape(item)}</li>" for item in items)


def _tradeoff_rows(decision: dict) -> str:
    rows = []
    recommended = decision.get("recommended_group")
    for group, comparison in decision.get("comparisons", {}).items():
        is_baseline = comparison.get("is_baseline", False)
        row_class = ' class="winner-row"' if group == recommended else ""
        badge = (
            '<span class="badge">Recomendado</span>'
            if group == recommended
            else ""
        )
        buyer_uplift = (
            "Baseline"
            if is_baseline
            else format_change(comparison.get("buyer_uplift_pct"))
        )
        net_change = (
            "Baseline"
            if is_baseline
            else format_change(comparison.get("net_value_change_pct"))
        )
        rows.append(f"""
            <tr{row_class}>
                <td><strong>{escape(group)}</strong>{badge}</td>
                <td>{comparison['percentual_cashback']:.2f}%</td>
                <td>{format_number(comparison['compradores'])}</td>
                <td>{buyer_uplift}</td>
                <td>{format_currency(comparison['valor_liquido'])}</td>
                <td>{net_change}</td>
                <td>{format_currency(comparison['valor_liquido_por_comprador'])}</td>
            </tr>
        """)
    return "".join(rows)


def _group_cards(kpis: dict, decision: dict) -> str:
    cards = []
    recommended = decision.get("recommended_group")
    for group, metrics in kpis.items():
        winner_class = " winner-card" if group == recommended else ""
        winner_label = (
            '<div class="winner-label">Variante recomendada</div>'
            if group == recommended
            else ""
        )
        observation = get_group_observation(group, metrics, decision)
        cards.append(f"""
            <article class="card{winner_class}">
                {winner_label}
                <h3>{escape(group)}</h3>
                <div class="metrics-grid">
                    <div class="metric-box">
                        <span class="metric-label">Cashback efetivo</span>
                        <span class="metric-value">{metrics['percentual_cashback']:.2f}%</span>
                    </div>
                    <div class="metric-box">
                        <span class="metric-label">Compradores</span>
                        <span class="metric-value">{format_number(metrics['compradores'])}</span>
                    </div>
                    <div class="metric-box">
                        <span class="metric-label">Valor líquido</span>
                        <span class="metric-value">{format_currency(metrics['valor_liquido'])}</span>
                    </div>
                    <div class="metric-box">
                        <span class="metric-label">Valor líquido / comprador</span>
                        <span class="metric-value">{format_currency(metrics['valor_liquido_por_comprador'])}</span>
                    </div>
                    <div class="metric-box">
                        <span class="metric-label">Vendas totais</span>
                        <span class="metric-value">{format_currency(metrics['vendas_totais'])}</span>
                    </div>
                    <div class="metric-box">
                        <span class="metric-label">Vendas / comprador</span>
                        <span class="metric-value">{format_currency(metrics['vendas_por_comprador'])}</span>
                    </div>
                </div>
                <p class="observation">{escape(observation)}</p>
            </article>
        """)
    return "".join(cards)


def generate_html_report(
    kpis: dict,
    parceiro: str = "Parceiro não informado",
    periodo_inicio: str = "Não informado",
    periodo_fim: str = "Não informado",
    output_path: str | Path = "reports/report.html",
    decision_result: dict | None = None,
) -> tuple[dict, int]:
    """Generate the executive report and return its decision and group count."""
    formatted_kpis = format_data(kpis)
    decision = decision_result or analyze_growth_tradeoff(formatted_kpis)
    recommended = decision.get("recommended_group")
    recommended_metrics = formatted_kpis.get(recommended, {})
    recommendation_title = (
        f"Escalar {escape(recommended)}"
        if recommended
        else "Recomendação indisponível"
    )
    cashback_rate = (
        f"{recommended_metrics.get('percentual_cashback', 0):.2f}%"
        if recommended
        else "N/D"
    )
    comparison_chart = graph_builder(
        kpis=formatted_kpis,
        recommended_group=recommended,
    )
    generated_at = datetime.now().strftime("%d/%m/%Y às %H:%M")
    group_count = len(formatted_kpis)
    tradeoff_rows = _tradeoff_rows(decision)
    cards = _group_cards(formatted_kpis, decision)

    html = f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Análise de Teste A/B - {escape(parceiro)}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; background: #f4f6f8; color: #1f2937; line-height: 1.55; }}
        .container {{ max-width: 1160px; margin: 0 auto; padding: 40px 24px 80px; }}
        .report-header {{ margin-bottom: 24px; }}
        .report-header h1 {{ margin: 0 0 6px; color: #111827; font-size: 32px; }}
        .subtitle {{ margin: 0; color: #64748b; }}
        .report-info, .decision-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin-top: 22px; }}
        .info-item, .decision-item {{ background: #fff; padding: 16px; border: 1px solid #e5e7eb; border-radius: 10px; }}
        .info-label, .metric-label {{ display: block; margin-bottom: 5px; color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: .03em; }}
        .info-value, .metric-value {{ color: #111827; font-weight: 700; }}
        section {{ margin-bottom: 28px; }}
        .section-box {{ background: #fff; padding: 28px; border-radius: 14px; box-shadow: 0 3px 12px rgba(15, 23, 42, .06); }}
        .recommendation-block {{ background: #ecfdf3; border-left: 6px solid #16a34a; }}
        .recommendation-block h2 {{ color: #166534; margin-bottom: 8px; }}
        .recommendation {{ margin: 0 0 14px; color: #14532d; font-size: 30px; font-weight: 800; }}
        .executive-summary {{ margin: 20px 0 0; font-size: 17px; }}
        h2 {{ margin: 0 0 14px; color: #111827; }}
        .two-columns {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 22px; margin-top: 20px; }}
        .two-columns h3 {{ margin: 0 0 8px; font-size: 16px; }}
        .two-columns ul {{ margin: 0; padding-left: 20px; }}
        .table-container {{ overflow-x: auto; }}
        table {{ width: 100%; min-width: 900px; border-collapse: collapse; margin-top: 18px; }}
        th {{ padding: 12px; text-align: left; background: #f1f5f9; color: #334155; font-size: 13px; }}
        td {{ padding: 14px 12px; border-bottom: 1px solid #e5e7eb; white-space: nowrap; }}
        tbody tr:nth-child(even) {{ background: #fafafa; }}
        .winner-row {{ background: #f0fdf4 !important; }}
        .badge {{ display: inline-block; margin-left: 7px; padding: 3px 7px; border-radius: 999px; background: #dcfce7; color: #166534; font-size: 10px; font-weight: 700; }}
        .note {{ margin-top: 16px; padding: 14px 16px; border-radius: 8px; background: #fff7ed; color: #9a3412; font-size: 14px; }}
        .cards-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .card {{ position: relative; background: #fff; padding: 24px; border: 1px solid #e5e7eb; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,.05); }}
        .winner-card {{ border: 2px solid #22c55e; }}
        .winner-label {{ position: absolute; top: -12px; right: 16px; padding: 5px 10px; border-radius: 999px; background: #16a34a; color: #fff; font-size: 11px; font-weight: 700; }}
        .card h3 {{ margin: 3px 0 18px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }}
        .metric-box {{ padding: 13px; background: #f8fafc; border-radius: 8px; }}
        .observation {{ margin: 18px 0 0; padding-top: 14px; border-top: 1px solid #e5e7eb; color: #475569; }}
        .chart-section {{ background: #fff; padding: 8px 0 0; }}
        .chart-header {{ text-align: center; margin-bottom: 20px; }}
        .chart-header h2 {{ margin-bottom: 7px; }}
        .chart-header p {{ margin: 0; color: #64748b; }}
        .chart-container {{ position: relative; height: 420px; }}
        .chart-note {{ display: flex; justify-content: center; align-items: center; gap: 6px; margin-top: 16px; color: #475569; font-size: 14px; }}
        .winner-indicator {{ width: 10px; height: 10px; border-radius: 50%; background: #16a34a; }}
        .footer {{ margin-top: 44px; padding-top: 22px; border-top: 1px solid #d1d5db; text-align: center; color: #64748b; font-size: 13px; }}
        @media (max-width: 600px) {{
            .container {{ padding: 24px 14px 50px; }}
            .section-box {{ padding: 20px; }}
            .report-header h1 {{ font-size: 27px; }}
            .recommendation {{ font-size: 24px; }}
            .metrics-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
<main class="container">
    <header class="report-header">
        <h1>Análise de Teste A/B de Cashback</h1>
        <p class="subtitle">Decisão determinística de Growth e sustentabilidade econômica</p>
        <div class="report-info">
            <div class="info-item"><span class="info-label">Parceiro</span><span class="info-value">{escape(parceiro)}</span></div>
            <div class="info-item"><span class="info-label">Período</span><span class="info-value">{escape(periodo_inicio)} a {escape(periodo_fim)}</span></div>
            <div class="info-item"><span class="info-label">Variantes</span><span class="info-value">{group_count}</span></div>
            <div class="info-item"><span class="info-label">Gerado em</span><span class="info-value">{generated_at}</span></div>
        </div>
    </header>

    <section class="section-box recommendation-block">
        <h2>Recomendação</h2>
        <p class="recommendation">{recommendation_title}</p>
        <div class="decision-grid">
            <div class="decision-item"><span class="info-label">Cashback efetivo</span><span class="info-value">{cashback_rate}</span></div>
            <div class="decision-item"><span class="info-label">Decisão</span><span class="info-value">{escape(decision['decision_label'])}</span></div>
            <div class="decision-item"><span class="info-label">Confiança</span><span class="info-value">{CONFIDENCE_LABELS.get(decision['confidence'], decision['confidence'])}</span></div>
            <div class="decision-item"><span class="info-label">Variante baseline</span><span class="info-value">{escape(decision.get('baseline_variant') or 'N/D')}</span></div>
        </div>
        <p class="executive-summary">{escape(decision['summary'])}</p>
        <div class="two-columns">
            <div><h3>Razões</h3><ul>{_list_items(decision['reasons'])}</ul></div>
            <div><h3>Trade-offs</h3><ul>{_list_items(decision['tradeoffs'])}</ul></div>
        </div>
    </section>

    <section class="section-box">
        <h2>Growth vs Resultado Econômico</h2>
        <p>A variante baseline é o grupo com a menor taxa efetiva de cashback; ela não é necessariamente um controle estatístico.</p>
        <div class="table-container">
            <table>
                <thead><tr><th>Grupo</th><th>Cashback efetivo</th><th>Compradores</th><th>Uplift de compradores</th><th>Valor líquido</th><th>Variação do valor líquido</th><th>Valor líquido / comprador</th></tr></thead>
                <tbody>{tradeoff_rows}</tbody>
            </table>
        </div>
        <p class="note"><strong>Limitação:</strong> o dataset não contém usuários expostos nem alocação de tráfego. Por isso, não é possível calcular conversão real. Compradores representa a resposta de Growth observada. A decisão usa resultados agregados e regras determinísticas, sem inferência de significância estatística.</p>
    </section>

    <section class="section-box">
        {comparison_chart}
    </section>

    <section>
        <h2>Detalhamento por Grupo</h2>
        <div class="cards-grid">{cards}</div>
    </section>

    <section class="section-box">
        <h2>Conclusão</h2>
        <p>{escape(decision['summary'])}</p>
        <p>Esta recomendação compara os resultados observados e não deve ser interpretada automaticamente como projeção linear para 100% do tráfego.</p>
    </section>

    <footer class="footer">Growth Strategy Analyzer<br>Relatório gerado automaticamente em {generated_at}</footer>
</main>
</body>
</html>
"""

    output_file = Path(output_path).resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html, encoding="utf-8")

    print("Report saved at:")
    print(output_file)
    print("Open report:")
    print(output_file.as_uri())

    return decision, group_count
