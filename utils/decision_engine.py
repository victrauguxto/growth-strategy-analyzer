"""Deterministic Growth versus economic-return decision engine."""

from __future__ import annotations

from typing import Any


MIN_BUYER_UPLIFT_PCT = 5.0
MAX_NET_VALUE_LOSS_PCT = 10.0
NEAR_TIE_PCT = 3.0

DECISION_LABELS = {
    "dominant_winner": "Liderança dominante",
    "balanced_growth": "Growth equilibrado",
    "growth_too_expensive": "Growth economicamente caro",
    "inefficient_incentive": "Incentivo ineficiente",
    "economic_winner": "Liderança econômica",
    "efficiency_tiebreaker": "Desempate por eficiência",
    "insufficient_variants": "Variantes insuficientes",
}

NUMERIC_FIELDS = (
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


def _number(value: Any) -> float:
    """Convert a KPI value to a finite float, defaulting to zero."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if number != number or number in (float("inf"), float("-inf")):
        return 0.0
    return number


def _normalize_kpis(kpis: dict | None) -> dict[str, dict[str, float]]:
    """Create a complete numeric KPI mapping without mutating the input."""
    if not isinstance(kpis, dict):
        return {}

    normalized: dict[str, dict[str, float]] = {}
    for group, metrics in kpis.items():
        if not isinstance(metrics, dict):
            metrics = {}
        normalized[str(group)] = {
            field: _number(metrics.get(field))
            for field in NUMERIC_FIELDS
        }
    return normalized


def _percent_change(current: float, baseline: float) -> float | None:
    """Calculate percentage change using the specified baseline formula."""
    if baseline == 0:
        return None
    return round(((current - baseline) / baseline) * 100, 2)


def _relative_difference(first: float, second: float) -> float:
    """Return the absolute symmetric difference used for near ties."""
    denominator = max(abs(first), abs(second))
    if denominator == 0:
        return 0.0
    return abs(first - second) / denominator * 100


def _rank(
    kpis: dict[str, dict[str, float]],
    metric: str,
) -> str:
    """Select a metric winner with stable, efficiency-aware tie breaks."""
    return sorted(
        kpis,
        key=lambda group: (
            -kpis[group][metric],
            kpis[group]["percentual_cashback"],
            group,
        ),
    )[0]


def _comparison(
    metrics: dict[str, float],
    baseline: dict[str, float],
    is_baseline: bool,
) -> dict[str, float | bool | None]:
    """Build baseline-relative trade-off metrics for one variant."""
    incremental_buyers = metrics["compradores"] - baseline["compradores"]
    incremental_cashback = metrics["cashback"] - baseline["cashback"]
    incremental_sales = metrics["vendas_totais"] - baseline["vendas_totais"]

    cashback_per_buyer = None
    sales_per_cashback = None
    if incremental_buyers > 0:
        cashback_per_buyer = round(
            incremental_cashback / incremental_buyers, 2
        )
        if incremental_cashback > 0:
            sales_per_cashback = round(
                incremental_sales / incremental_cashback, 2
            )

    return {
        **metrics,
        "is_baseline": is_baseline,
        "buyer_uplift_pct": 0.0 if is_baseline else _percent_change(
            metrics["compradores"], baseline["compradores"]
        ),
        "net_value_change_pct": 0.0 if is_baseline else _percent_change(
            metrics["valor_liquido"], baseline["valor_liquido"]
        ),
        "sales_change_pct": 0.0 if is_baseline else _percent_change(
            metrics["vendas_totais"], baseline["vendas_totais"]
        ),
        "cashback_rate_increase_pp": round(
            metrics["percentual_cashback"]
            - baseline["percentual_cashback"],
            2,
        ),
        "net_value_per_buyer_change_pct": (
            0.0 if is_baseline else _percent_change(
                metrics["valor_liquido_por_comprador"],
                baseline["valor_liquido_por_comprador"],
            )
        ),
        "incremental_cashback": 0.0 if is_baseline else round(
            incremental_cashback, 2
        ),
        "incremental_buyers": 0.0 if is_baseline else round(
            incremental_buyers, 2
        ),
        "incremental_sales": 0.0 if is_baseline else round(
            incremental_sales, 2
        ),
        "incremental_cashback_per_additional_buyer": (
            None if is_baseline else cashback_per_buyer
        ),
        "incremental_sales_per_additional_cashback_real": (
            None if is_baseline else sales_per_cashback
        ),
    }


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "não calculável"
    return f"{value:+.1f}%"


def _base_result(
    normalized: dict[str, dict[str, float]],
) -> tuple[
    str,
    str,
    str,
    str,
    dict[str, dict[str, float | bool | None]],
]:
    baseline = sorted(
        normalized,
        key=lambda group: (
            normalized[group]["percentual_cashback"],
            -normalized[group]["valor_liquido"],
            group,
        ),
    )[0]
    economic = _rank(normalized, "valor_liquido")
    growth = _rank(normalized, "compradores")
    efficiency = _rank(normalized, "valor_liquido_por_comprador")
    comparisons = {
        group: _comparison(
            metrics,
            normalized[baseline],
            group == baseline,
        )
        for group, metrics in normalized.items()
    }
    return baseline, economic, growth, efficiency, comparisons


def _result(
    *,
    recommended: str | None,
    economic: str | None,
    growth: str | None,
    efficiency: str | None,
    baseline: str | None,
    decision_type: str,
    confidence: str,
    summary: str,
    reasons: list[str],
    tradeoffs: list[str],
    comparisons: dict,
    tradeoff_group: str | None = None,
) -> dict:
    """Build the stable public result consumed by every output adapter."""
    return {
        "recommended_group": recommended,
        "economic_winner": economic,
        "growth_winner": growth,
        "efficiency_winner": efficiency,
        "baseline_variant": baseline,
        "decision_type": decision_type,
        "decision_label": DECISION_LABELS[decision_type],
        "confidence": confidence,
        "summary": summary,
        "reasons": reasons,
        "tradeoffs": tradeoffs,
        "comparisons": comparisons,
        "tradeoff_group": tradeoff_group or recommended,
        # Compatibility aliases for existing integrations.
        "grupo": recommended,
        "justificativa": summary,
    }


def analyze_growth_tradeoff(kpis: dict) -> dict:
    """Recommend a cashback variant using explicit deterministic rules.

    Buyers represent observed customer response. This engine does not infer
    conversion because the datasets contain neither exposed users nor traffic
    allocation. No statistical significance is calculated.
    """
    normalized = _normalize_kpis(kpis)
    if len(normalized) < 2:
        return _result(
            recommended=None,
            economic=next(iter(normalized), None),
            growth=next(iter(normalized), None),
            efficiency=next(iter(normalized), None),
            baseline=next(iter(normalized), None),
            decision_type="insufficient_variants",
            confidence="low",
            summary=(
                "Não há variantes suficientes para comparar Growth e retorno "
                "econômico. É necessário ter pelo menos dois grupos."
            ),
            reasons=["Uma comparação A/B exige pelo menos duas variantes."],
            tradeoffs=["Nenhum trade-off entre variantes pôde ser calculado."],
            comparisons={},
        )

    baseline, economic, growth, efficiency, comparisons = _base_result(
        normalized
    )

    finalists = [economic]
    if growth != economic:
        finalists.append(growth)
    else:
        alternatives = {
            group: normalized[group]
            for group in normalized
            if group != economic
        }
        finalists.append(_rank(alternatives, "valor_liquido"))

    first, second = finalists
    buyer_gap = _relative_difference(
        normalized[first]["compradores"],
        normalized[second]["compradores"],
    )
    net_gap = _relative_difference(
        normalized[first]["valor_liquido"],
        normalized[second]["valor_liquido"],
    )
    if buyer_gap < NEAR_TIE_PCT and net_gap < NEAR_TIE_PCT:
        recommended = sorted(
            (first, second),
            key=lambda group: (
                normalized[group]["percentual_cashback"],
                -normalized[group]["valor_liquido_por_comprador"],
                group,
            ),
        )[0]
        summary = (
            f"{first} e {second} ficaram a menos de 3% de diferença em "
            "compradores e valor líquido. O desempate favorece "
            f"{recommended}, que exige a menor taxa efetiva de cashback e "
            "preserva maior eficiência por comprador."
        )
        return _result(
            recommended=recommended,
            economic=economic,
            growth=growth,
            efficiency=efficiency,
            baseline=baseline,
            decision_type="efficiency_tiebreaker",
            confidence="low",
            summary=summary,
            reasons=[
                f"Diferença de compradores entre finalistas: {buyer_gap:.1f}%.",
                f"Diferença de valor líquido entre finalistas: {net_gap:.1f}%.",
            ],
            tradeoffs=[
                "Com resultados próximos, o menor incentivo reduz custo sem "
                "sacrificar materialmente a resposta observada."
            ],
            comparisons=comparisons,
            tradeoff_group=(
                second if recommended == first else first
            ),
        )

    if economic == growth:
        inefficient_alternatives = [
            group
            for group, comparison in comparisons.items()
            if group != baseline
            and comparison["cashback_rate_increase_pp"] > 0
            and comparison["buyer_uplift_pct"] is not None
            and comparison["buyer_uplift_pct"] < NEAR_TIE_PCT
            and comparison["net_value_change_pct"] is not None
            and comparison["net_value_change_pct"] < 0
        ]
        if economic == baseline and inefficient_alternatives:
            rejected = sorted(
                inefficient_alternatives,
                key=lambda group: (
                    -normalized[group]["percentual_cashback"],
                    group,
                ),
            )[0]
            comparison = comparisons[rejected]
            summary = (
                f"{rejected} exigiu cashback efetivo maior, sem ganho material "
                "de compradores, e ainda reduziu o valor líquido. O incentivo "
                f"é ineficiente; por isso, {economic} é recomendado."
            )
            return _result(
                recommended=economic,
                economic=economic,
                growth=growth,
                efficiency=efficiency,
                baseline=baseline,
                decision_type="inefficient_incentive",
                confidence="high",
                summary=summary,
                reasons=[
                    "Variação de compradores de "
                    f"{_fmt_pct(comparison['buyer_uplift_pct'])}.",
                    "Variação de valor líquido de "
                    f"{_fmt_pct(comparison['net_value_change_pct'])}.",
                ],
                tradeoffs=[
                    "Um incentivo maior não produziu resposta adicional "
                    "suficiente."
                ],
                comparisons=comparisons,
                tradeoff_group=rejected,
            )

        alternatives = [group for group in normalized if group != economic]
        best_alternative = _rank(
            {group: normalized[group] for group in alternatives},
            "valor_liquido",
        )
        summary = (
            f"{economic} apresentou simultaneamente o maior volume de "
            "compradores e o maior valor líquido, liderando a resposta de "
            "clientes e o resultado econômico direto."
        )
        return _result(
            recommended=economic,
            economic=economic,
            growth=growth,
            efficiency=efficiency,
            baseline=baseline,
            decision_type="dominant_winner",
            confidence="high",
            summary=summary,
            reasons=[
                f"{economic} liderou compradores e valor líquido.",
                f"A alternativa econômica seguinte foi {best_alternative}.",
            ],
            tradeoffs=[
                "Não foi necessário aceitar perda econômica para obter a "
                "melhor resposta de compradores."
            ],
            comparisons=comparisons,
        )

    growth_candidates = [
        group
        for group, comparison in comparisons.items()
        if group != baseline
        and comparison["cashback_rate_increase_pp"] > 0
        and comparison["buyer_uplift_pct"] is not None
        and comparison["buyer_uplift_pct"] > 0
    ]
    balanced_candidates = [
        group
        for group in growth_candidates
        if comparisons[group]["buyer_uplift_pct"] >= MIN_BUYER_UPLIFT_PCT
        and comparisons[group]["net_value_change_pct"] is not None
        and -MAX_NET_VALUE_LOSS_PCT
        <= comparisons[group]["net_value_change_pct"]
        <= 0
        and comparisons[group]["buyer_uplift_pct"]
        > abs(comparisons[group]["net_value_change_pct"])
    ]
    if balanced_candidates:
        recommended = sorted(
            balanced_candidates,
            key=lambda group: (
                -normalized[group]["compradores"],
                -normalized[group]["valor_liquido"],
                normalized[group]["percentual_cashback"],
                group,
            ),
        )[0]
        comparison = comparisons[recommended]
        uplift = comparison["buyer_uplift_pct"]
        net_change = comparison["net_value_change_pct"]
        confidence = (
            "high"
            if uplift >= 10 and abs(net_change) <= 5
            else "medium"
        )
        summary = (
            f"{recommended} aumentou compradores em {_fmt_pct(uplift)} frente "
            f"à variante baseline {baseline}, com variação de valor líquido "
            f"de {_fmt_pct(net_change)}. O ganho de Growth é proporcionalmente "
            "superior à perda econômica e permanece dentro do limite de 10%, "
            f"portanto {recommended} é recomendado."
        )
        return _result(
            recommended=recommended,
            economic=economic,
            growth=growth,
            efficiency=efficiency,
            baseline=baseline,
            decision_type="balanced_growth",
            confidence=confidence,
            summary=summary,
            reasons=[
                f"Uplift de compradores: {_fmt_pct(uplift)}.",
                f"Variação de valor líquido: {_fmt_pct(net_change)}.",
            ],
            tradeoffs=[
                "O cashback efetivo aumentou "
                f"{comparison['cashback_rate_increase_pp']:+.2f} p.p.",
                "A perda econômica observada ficou abaixo do limite de 10%.",
            ],
            comparisons=comparisons,
        )

    expensive_candidates = [
        group
        for group in growth_candidates
        if comparisons[group]["net_value_change_pct"] is not None
        and comparisons[group]["net_value_change_pct"]
        < -MAX_NET_VALUE_LOSS_PCT
        and abs(comparisons[group]["net_value_change_pct"])
        > comparisons[group]["buyer_uplift_pct"]
    ]
    if expensive_candidates:
        expensive = sorted(
            expensive_candidates,
            key=lambda group: -comparisons[group]["buyer_uplift_pct"],
        )[0]
        comparison = comparisons[expensive]
        uplift = comparison["buyer_uplift_pct"]
        net_change = comparison["net_value_change_pct"]
        confidence = (
            "high" if abs(net_change) - uplift >= 10 else "medium"
        )
        summary = (
            f"{expensive} gerou {_fmt_pct(uplift)} mais compradores que a "
            f"variante baseline {baseline}, mas seu valor líquido variou "
            f"{_fmt_pct(net_change)}. O custo econômico foi desproporcional ao "
            f"Growth observado; por isso, {economic} é recomendado."
        )
        return _result(
            recommended=economic,
            economic=economic,
            growth=growth,
            efficiency=efficiency,
            baseline=baseline,
            decision_type="growth_too_expensive",
            confidence=confidence,
            summary=summary,
            reasons=[
                f"{expensive} elevou compradores em {_fmt_pct(uplift)}.",
                f"A perda de valor líquido foi {_fmt_pct(net_change)}.",
            ],
            tradeoffs=[
                "A perda econômica superou tanto 10% quanto o ganho "
                "proporcional de compradores."
            ],
            comparisons=comparisons,
            tradeoff_group=expensive,
        )

    inefficient = [
        group
        for group, comparison in comparisons.items()
        if group != baseline
        and comparison["cashback_rate_increase_pp"] > 0
        and comparison["buyer_uplift_pct"] is not None
        and comparison["buyer_uplift_pct"] < NEAR_TIE_PCT
        and comparison["net_value_change_pct"] is not None
        and comparison["net_value_change_pct"] < 0
    ]
    if inefficient:
        rejected = sorted(
            inefficient,
            key=lambda group: (
                -normalized[group]["percentual_cashback"],
                group,
            ),
        )[0]
        comparison = comparisons[rejected]
        summary = (
            f"{rejected} exigiu cashback efetivo maior, sem ganho material de "
            "compradores, e ainda reduziu o valor líquido. O incentivo é "
            f"ineficiente; por isso, {economic} é recomendado."
        )
        return _result(
            recommended=economic,
            economic=economic,
            growth=growth,
            efficiency=efficiency,
            baseline=baseline,
            decision_type="inefficient_incentive",
            confidence="high",
            summary=summary,
            reasons=[
                "Variação de compradores de "
                f"{_fmt_pct(comparison['buyer_uplift_pct'])}.",
                "Variação de valor líquido de "
                f"{_fmt_pct(comparison['net_value_change_pct'])}.",
            ],
            tradeoffs=[
                "Um incentivo maior não produziu resposta adicional suficiente."
            ],
            comparisons=comparisons,
            tradeoff_group=rejected,
        )

    growth_comparison = comparisons[growth]
    economic_alternatives = {
        group: normalized[group]
        for group in normalized
        if group != economic
    }
    next_economic = _rank(economic_alternatives, "valor_liquido")
    net_advantage = _relative_difference(
        normalized[economic]["valor_liquido"],
        normalized[next_economic]["valor_liquido"],
    )
    growth_uplift = growth_comparison["buyer_uplift_pct"]
    confidence = (
        "high"
        if net_advantage >= 10
        and (growth_uplift is None or growth_uplift < MIN_BUYER_UPLIFT_PCT)
        else "medium"
    )
    summary = (
        f"{economic} apresentou o maior valor líquido. As demais variantes "
        "não geraram compradores adicionais suficientes para justificar a "
        f"redução do retorno econômico, portanto {economic} é recomendado."
    )
    return _result(
        recommended=economic,
        economic=economic,
        growth=growth,
        efficiency=efficiency,
        baseline=baseline,
        decision_type="economic_winner",
        confidence=confidence,
        summary=summary,
        reasons=[
            f"{economic} liderou o valor líquido total.",
            f"{growth} liderou compradores, mas não atendeu aos critérios de "
            "Growth equilibrado.",
        ],
        tradeoffs=[
            "Uplift do líder de compradores versus baseline: "
            f"{_fmt_pct(growth_comparison['buyer_uplift_pct'])}.",
            "Variação de valor líquido do líder de compradores: "
            f"{_fmt_pct(growth_comparison['net_value_change_pct'])}.",
        ],
        comparisons=comparisons,
        tradeoff_group=growth,
    )
