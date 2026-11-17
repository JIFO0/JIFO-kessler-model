"""
Moduł analizy statystycznej i ekonometrycznej:
dekompozycja wrażliwości, tabele percentyli oraz elastyczności polityk regulacyjnych.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List


def summarize_fan_chart_table(fan_dict: Dict[str, np.ndarray],
                              years: np.ndarray,
                              milestone_years: List[int] = [2030, 2040, 2050, 2060, 2075, 2100, 2126]) -> pd.DataFrame:
    """
    Tworzy tabelę podsumowującą percentyle (p10, p25, median, p75, p90) dla kluczowych lat.
    """
    rows = []
    for my in milestone_years:
        if my in years:
            idx = int(np.where(years == my)[0][0])
            rows.append({
                "Rok": my,
                "10% (Optymistyczny)": round(float(fan_dict["p10"][idx]), 4),
                "25%": round(float(fan_dict["p25"][idx]), 4),
                "Mediana (50%)": round(float(fan_dict["p50"][idx]), 4),
                "75%": round(float(fan_dict["p75"][idx]), 4),
                "90% (Pesymistyczny)": round(float(fan_dict["p90"][idx]), 4)
            })
    return pd.DataFrame(rows)


def analyze_sensitivity(mc_results: Dict[str, Any],
                       target_col: str = "P_Kessler_any_2100") -> pd.DataFrame:
    """
    Wykonuje analizę wrażliwości (standaryzowane współczynniki wielowymiarowej regresji OLS i korelacje)
    pomiędzy parametrami wejściowymi a ryzykiem kaskady Kesslera w roku 2100.
    """
    df = mc_results["raw_terminal_df"]
    if target_col not in df.columns:
        raise ValueError(f"Kolumna docelowa {target_col} nie istnieje w wynikach.")
        
    # Zmienne wejściowe (parametry a priori)
    feature_cols = ["beta_multiplier", "growth_multiplier", "pmd_compliance_shift"]
    
    y = df[target_col].values.astype(float)
    std_y = np.std(y)
    
    if std_y < 1e-9:
        # Brak wariancji w zmiennej docelowej
        return pd.DataFrame([
            {"Parametr": col, "Korelacja z Ryzykiem": 0.0, "Standaryzowany Wpływ (Beta)": 0.0, "Kierunek Wpływu": "Brak zmienności"}
            for col in feature_cols
        ])
        
    y_std = (y - np.mean(y)) / std_y
    
    # Standaryzacja macierzy cech X
    X_mat = df[feature_cols].values.astype(float)
    X_std = (X_mat - np.mean(X_mat, axis=0)) / (np.std(X_mat, axis=0) + 1e-9)
    
    # Wielowymiarowe standaryzowane wagi regresji OLS (Beta weights)
    try:
        betas, _, _, _ = np.linalg.lstsq(X_std, y_std, rcond=None)
    except Exception:
        betas = np.zeros(len(feature_cols))
    
    records = []
    for idx, col in enumerate(feature_cols):
        x = df[col].values.astype(float)
        std_x = np.std(x)
        corr = float(np.corrcoef(x, y)[0, 1]) if std_x > 1e-9 else 0.0
        beta_val = float(betas[idx])
        
        records.append({
            "Parametr": col,
            "Korelacja z Ryzykiem": round(corr, 4),
            "Standaryzowany Wpływ (Beta)": round(beta_val, 4),
            "Kierunek Wpływu": "Zwiększa ryzyko" if beta_val > 0 else "Zmniejsza ryzyko"
        })
        
    res_df = pd.DataFrame(records).sort_values(by="Standaryzowany Wpływ (Beta)", key=abs, ascending=False)
    return res_df.reset_index(drop=True)


def compute_policy_scenarios(base_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Porównuje bazową trajektorię deterministyczną z kluczowymi scenariuszami polityki orbitalnej:
    1. Status Quo / Baseline
    2. Surowa regulacja (PMD 98-99%, spowolnienie g=2%)
    3. Niekontrolowana ekspansja megakonstelacji (Starship era: g=10%, PMD 80%)
    """
    from src.config import SHELL_CONFIGS
    from src.simulation import run_deterministic
    import copy
    
    # Scenariusz 1: Regulacja 'Zero Debris' (wysoki PMD)
    cfg_zero_debris = copy.deepcopy(SHELL_CONFIGS)
    for k in cfg_zero_debris:
        cfg_zero_debris[k].q_pmd = min(0.99, cfg_zero_debris[k].q_pmd + 0.04)
        cfg_zero_debris[k].g_rate = max(0.015, cfg_zero_debris[k].g_rate * 0.7)
    df_zero_debris = run_deterministic(custom_configs=cfg_zero_debris)
    
    # Scenariusz 2: Niekontrolowana ekspansja (Starship / tani dostęp)
    cfg_expansion = copy.deepcopy(SHELL_CONFIGS)
    for k in cfg_expansion:
        cfg_expansion[k].q_pmd = max(0.70, cfg_expansion[k].q_pmd - 0.10)
        cfg_expansion[k].g_rate = cfg_expansion[k].g_rate * 2.0
        cfg_expansion[k].K_launch = cfg_expansion[k].K_launch * 2.5
        cfg_expansion[k].cam_eff_X_D10 = max(0.80, cfg_expansion[k].cam_eff_X_D10 - 0.05)
    df_expansion = run_deterministic(custom_configs=cfg_expansion)
    
    return {
        "baseline": base_df,
        "zero_debris_charter": df_zero_debris,
        "uncontrolled_expansion": df_expansion
    }
