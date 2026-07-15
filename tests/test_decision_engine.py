"""Business-rule validation scenarios for the deterministic engine."""

import unittest

from utils.decision_engine import analyze_growth_tradeoff


def metrics(
    cashback_rate: float,
    buyers: int,
    net_value: float,
    sales: float = 1_000.0,
) -> dict:
    cashback = sales * cashback_rate / 100
    commission = cashback + net_value
    return {
        "percentual_cashback": cashback_rate,
        "percentual_comissao": commission / sales * 100,
        "compradores": buyers,
        "vendas_totais": sales,
        "comissao": commission,
        "cashback": cashback,
        "valor_liquido": net_value,
        "valor_liquido_por_comprador": (
            net_value / buyers if buyers else 0
        ),
        "vendas_por_comprador": sales / buyers if buyers else 0,
    }


class DecisionEngineScenarios(unittest.TestCase):
    def test_clear_dominant_winner(self) -> None:
        result = analyze_growth_tradeoff({
            "Grupo 1": metrics(4.0, 100, 100),
            "Grupo 2": metrics(5.0, 115, 112),
        })

        self.assertEqual(result["recommended_group"], "Grupo 2")
        self.assertEqual(result["decision_type"], "dominant_winner")
        self.assertEqual(result["confidence"], "high")

    def test_balanced_growth_winner(self) -> None:
        result = analyze_growth_tradeoff({
            "Grupo 1": metrics(4.0, 100, 100),
            "Grupo 2": metrics(5.0, 115, 95),
        })

        self.assertEqual(result["recommended_group"], "Grupo 2")
        self.assertEqual(result["decision_type"], "balanced_growth")
        self.assertEqual(
            result["comparisons"]["Grupo 2"]["buyer_uplift_pct"],
            15.0,
        )
        self.assertEqual(
            result["comparisons"]["Grupo 2"]["net_value_change_pct"],
            -5.0,
        )

    def test_growth_too_expensive(self) -> None:
        result = analyze_growth_tradeoff({
            "Grupo 1": metrics(4.0, 100, 100),
            "Grupo 2": metrics(5.0, 108, 75),
        })

        self.assertEqual(result["recommended_group"], "Grupo 1")
        self.assertEqual(result["decision_type"], "growth_too_expensive")

    def test_inefficient_higher_cashback(self) -> None:
        result = analyze_growth_tradeoff({
            "Grupo 1": metrics(4.0, 100, 100),
            "Grupo 2": metrics(6.0, 90, 80),
        })

        self.assertEqual(result["recommended_group"], "Grupo 1")
        self.assertEqual(result["decision_type"], "inefficient_incentive")

    def test_near_tie_prefers_lower_cashback(self) -> None:
        result = analyze_growth_tradeoff({
            "Grupo 1": metrics(4.0, 100, 100),
            "Grupo 2": metrics(5.0, 102, 101),
        })

        self.assertEqual(result["recommended_group"], "Grupo 1")
        self.assertEqual(result["decision_type"], "efficiency_tiebreaker")
        self.assertEqual(result["confidence"], "low")

    def test_incremental_efficiency_and_baseline(self) -> None:
        result = analyze_growth_tradeoff({
            "Grupo 1": metrics(4.0, 100, 100, 1_000),
            "Grupo 2": metrics(5.0, 110, 95, 1_200),
        })
        comparison = result["comparisons"]["Grupo 2"]

        self.assertEqual(result["baseline_variant"], "Grupo 1")
        self.assertEqual(comparison["incremental_buyers"], 10)
        self.assertEqual(comparison["incremental_cashback"], 20)
        self.assertEqual(
            comparison["incremental_cashback_per_additional_buyer"], 2
        )
        self.assertEqual(
            comparison["incremental_sales_per_additional_cashback_real"],
            10,
        )

    def test_one_group_does_not_create_fake_recommendation(self) -> None:
        result = analyze_growth_tradeoff({
            "Grupo 1": metrics(4.0, 100, 100),
        })

        self.assertIsNone(result["recommended_group"])
        self.assertEqual(result["decision_type"], "insufficient_variants")
        self.assertEqual(result["confidence"], "low")

    def test_empty_kpis_are_handled(self) -> None:
        result = analyze_growth_tradeoff({})
        self.assertIsNone(result["recommended_group"])
        self.assertEqual(result["decision_type"], "insufficient_variants")

    def test_zero_baseline_denominators_return_none(self) -> None:
        result = analyze_growth_tradeoff({
            "Grupo 1": {},
            "Grupo 2": metrics(5.0, 10, 20, 100),
        })
        comparison = result["comparisons"]["Grupo 2"]

        self.assertIsNone(comparison["buyer_uplift_pct"])
        self.assertIsNone(comparison["net_value_change_pct"])
        self.assertIsNone(comparison["sales_change_pct"])

    def test_missing_kpi_values_do_not_crash(self) -> None:
        result = analyze_growth_tradeoff({
            "Grupo 1": {"compradores": None},
            "Grupo 2": {"valor_liquido": "invalid"},
        })

        self.assertIn(result["decision_type"], {
            "efficiency_tiebreaker",
            "economic_winner",
        })


if __name__ == "__main__":
    unittest.main()
