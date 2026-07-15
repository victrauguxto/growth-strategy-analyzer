"""KPI aggregation tests."""

import unittest

import pandas as pd

from utils.csv_reader import extract_kpis


class KpiAggregationTests(unittest.TestCase):
    def test_effective_rates_use_ratio_of_totals(self) -> None:
        df = pd.DataFrame({
            "grupos_de_usuarios": ["Grupo 1", "Grupo 1"],
            "compradores": [10, 90],
            "vendas_totais": [100.0, 900.0],
            "comissao": [10.0, 180.0],
            "cashback": [1.0, 90.0],
        })

        kpi = extract_kpis(df)["Grupo 1"]

        self.assertEqual(kpi["percentual_cashback"], 9.1)
        self.assertEqual(kpi["percentual_comissao"], 19.0)
        self.assertEqual(kpi["vendas_totais"], 1_000.0)
        self.assertEqual(kpi["valor_liquido"], 99.0)
        self.assertEqual(kpi["valor_liquido_por_comprador"], 0.99)
        self.assertEqual(kpi["vendas_por_comprador"], 10.0)

    def test_zero_buyers_and_sales_are_safe(self) -> None:
        df = pd.DataFrame({
            "grupos_de_usuarios": ["Grupo 1"],
            "compradores": [0],
            "vendas_totais": [0.0],
            "comissao": [0.0],
            "cashback": [0.0],
        })

        kpi = extract_kpis(df)["Grupo 1"]
        self.assertEqual(kpi["percentual_cashback"], 0.0)
        self.assertEqual(kpi["percentual_comissao"], 0.0)
        self.assertEqual(kpi["valor_liquido_por_comprador"], 0.0)
        self.assertEqual(kpi["vendas_por_comprador"], 0.0)


if __name__ == "__main__":
    unittest.main()
