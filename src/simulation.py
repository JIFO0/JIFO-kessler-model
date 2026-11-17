"""
Silnik symulacji: trajektorie deterministyczne oraz wielowątkowy silnik Monte Carlo.
"""

import copy
import time
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from src.config import (
    SHELL_CONFIGS, ShellParameters, SIMULATION_CONFIG, HAZARD_CONFIG
)
from src.models import CoupledOrbitalSystem, OrbitalShellModel


def run_deterministic(start_year: int = 2026,
                      end_year: int = 2126,
                      dt: float = 1.0,
                      custom_configs: Optional[Dict[str, ShellParameters]] = None) -> pd.DataFrame:
    """
    Uruchamia pojedynczą deterministyczną symulację bazową dla wszystkich 4 modeli.
    Zwraca pandas DataFrame ze wszystkimi trajektoriami.
    """
    system = CoupledOrbitalSystem(custom_configs=custom_configs)
    years = np.arange(start_year, end_year + dt, dt)
    records = []
    
    for y in years:
        step_res = system.step(y, dt)
        row = {
            "year": y,
            "P_Kessler_any": step_res["P_Kessler_any"],
            "P_catastrophic_any": step_res.get("P_catastrophic_any", 0.0)
        }
        for shell_name in ["low", "medium", "high", "global"]:
            sr = step_res[shell_name]
            row[f"{shell_name}_X"] = sr["X"]
            row[f"{shell_name}_D10"] = sr["D10"]
            row[f"{shell_name}_D1"] = sr["D1"]
            row[f"{shell_name}_D01"] = sr["D01"]
            row[f"{shell_name}_N_total"] = sr["N_total"]
            row[f"{shell_name}_R_K"] = sr["R_K"]
            row[f"{shell_name}_hazard"] = sr["hazard"]
            row[f"{shell_name}_P_Kessler"] = sr["P_Kessler"]
            row[f"{shell_name}_P_catastrophic"] = sr.get("P_catastrophic", 0.0)
            row[f"{shell_name}_collisions"] = sr["collisions_annual"]
            
        records.append(row)
        
    return pd.DataFrame(records)


def sample_shell_configs(seed: Optional[int] = None,
                         base_configs: Optional[Dict[str, ShellParameters]] = None) -> Tuple[Dict[str, ShellParameters], Dict[str, float]]:
    """
    Losuje spójny zestaw parametrów z rozkładów a priori dla symulacji Monte Carlo.
    Zwraca słownik nowych konfiguracji oraz wektor wylosowanych parametrów (do analizy wrażliwości).
    """
    rng = np.random.default_rng(seed)
    sampled_configs = {}
    sampled_params_summary = {}
    
    # Źródło bazowych konfiguracji
    active_base = base_configs if base_configs is not None else SHELL_CONFIGS
    
    # Globalne czynniki ekonomiczne i technologiczne
    growth_multiplier = rng.normal(1.0, 0.25)
    growth_multiplier = max(0.2, min(2.5, growth_multiplier))
    
    beta_multiplier = rng.lognormal(mean=0.0, sigma=0.35)
    beta_multiplier = max(0.3, min(3.5, beta_multiplier))
    
    pmd_compliance_shift = rng.normal(0.0, 0.04)
    pmd_compliance_shift = max(-0.15, min(0.04, pmd_compliance_shift))
    
    sampled_params_summary["growth_multiplier"] = growth_multiplier
    sampled_params_summary["beta_multiplier"] = beta_multiplier
    sampled_params_summary["pmd_compliance_shift"] = pmd_compliance_shift
    
    for key, base in active_base.items():
        p = copy.deepcopy(base)
        
        # 1. Losowanie stopy wzrostu startów g_rate
        p.g_rate = max(0.005, min(0.20, base.g_rate * growth_multiplier))
        p.K_launch = base.K_launch * max(0.5, min(3.0, growth_multiplier))
        
        # 2. Losowanie fragmentacji beta
        p.beta_10_sat = base.beta_10_sat * beta_multiplier
        p.beta_1_sat = base.beta_1_sat * beta_multiplier
        p.beta_10_dd = base.beta_10_dd * beta_multiplier
        p.beta_1_dd = base.beta_1_dd * beta_multiplier
        p.beta_10_pebble = base.beta_10_pebble * beta_multiplier
        p.beta_1_pebble = base.beta_1_pebble * beta_multiplier
        
        # 3. Losowanie skuteczności deorbitacji PMD (q_pmd)
        p.q_pmd = max(0.50, min(0.999, base.q_pmd + pmd_compliance_shift))
        
        # 4. Losowanie czasu życia w atmosferze tau_decay (niepewność modeli atmosfery)
        tau_perturb = rng.lognormal(0.0, 0.20)
        p.tau_decay_base = base.tau_decay_base * tau_perturb
        
        # 5. Losowanie współczynnika koncentracji przestrzennej theta
        theta_perturb = rng.lognormal(0.0, 0.25)
        p.theta_eff = max(0.001, min(0.5, base.theta_eff * theta_perturb))
        
        sampled_configs[key] = p
        
    return sampled_configs, sampled_params_summary


def run_monte_carlo(n_samples: int = 1000,
                     start_year: int = 2026,
                     end_year: int = 2126,
                     dt: float = 1.0,
                     seed: int = 42,
                     custom_configs: Optional[Dict[str, ShellParameters]] = None) -> Dict[str, Any]:
    """
    Wydajny silnik symulacji Monte Carlo.
    Zwraca percentyle fan-chartów dla P(K_t), R_K(t), N(t) oraz zrzut próbek do analizy wrażliwości.
    """
    t0 = time.time()
    years = np.arange(start_year, end_year + dt, dt)
    n_years = len(years)
    
    # Macierze wynikowe [n_samples, n_years]
    p_kessler_any = np.zeros((n_samples, n_years))
    p_kessler_low = np.zeros((n_samples, n_years))
    p_kessler_med = np.zeros((n_samples, n_years))
    p_kessler_high = np.zeros((n_samples, n_years))
    p_kessler_glob = np.zeros((n_samples, n_years))
    
    p_catastrophic_any = np.zeros((n_samples, n_years))
    
    rk_med = np.zeros((n_samples, n_years))
    rk_low = np.zeros((n_samples, n_years))
    rk_high = np.zeros((n_samples, n_years))
    rk_glob = np.zeros((n_samples, n_years))
    
    n_total_med = np.zeros((n_samples, n_years))
    n_total_glob = np.zeros((n_samples, n_years))
    
    mc_params_list = []
    
    base_rng = np.random.default_rng(seed)
    sample_seeds = base_rng.integers(1, 100000000, size=n_samples)
    
    for s_idx in range(n_samples):
        s_seed = int(sample_seeds[s_idx])
        sampled_configs, s_summary = sample_shell_configs(seed=s_seed, base_configs=custom_configs)
        
        system = CoupledOrbitalSystem(custom_configs=sampled_configs)
        
        for y_idx, y in enumerate(years):
            res = system.step(y, dt)
            p_kessler_any[s_idx, y_idx] = res["P_Kessler_any"]
            p_kessler_low[s_idx, y_idx] = res["low"]["P_Kessler"]
            p_kessler_med[s_idx, y_idx] = res["medium"]["P_Kessler"]
            p_kessler_high[s_idx, y_idx] = res["high"]["P_Kessler"]
            p_kessler_glob[s_idx, y_idx] = res["global"]["P_Kessler"]
            
            p_catastrophic_any[s_idx, y_idx] = res.get("P_catastrophic_any", 0.0)
            
            rk_low[s_idx, y_idx] = res["low"]["R_K"]
            rk_med[s_idx, y_idx] = res["medium"]["R_K"]
            rk_high[s_idx, y_idx] = res["high"]["R_K"]
            rk_glob[s_idx, y_idx] = res["global"]["R_K"]
            
            n_total_med[s_idx, y_idx] = res["medium"]["N_total"]
            n_total_glob[s_idx, y_idx] = res["global"]["N_total"]
            
        # Zapis metryk kluczowych dla pojedynczej próbki (2050, 2060, 2100)
        idx_2050 = int(np.where(years == 2050)[0][0]) if 2050 in years else -1
        idx_2060 = int(np.where(years == 2060)[0][0]) if 2060 in years else -1
        idx_2100 = int(np.where(years == 2100)[0][0]) if 2100 in years else -1
        
        s_summary["P_Kessler_med_2050"] = p_kessler_med[s_idx, idx_2050]
        s_summary["P_Kessler_med_2060"] = p_kessler_med[s_idx, idx_2060]
        s_summary["P_Kessler_med_2100"] = p_kessler_med[s_idx, idx_2100]
        s_summary["P_Kessler_any_2050"] = p_kessler_any[s_idx, idx_2050]
        s_summary["P_Kessler_any_2100"] = p_kessler_any[s_idx, idx_2100]
        s_summary["R_K_med_2060"] = rk_med[s_idx, idx_2060]
        s_summary["R_K_med_final"] = rk_med[s_idx, -1]
        mc_params_list.append(s_summary)
        
    elapsed = time.time() - t0
    
    # Obliczanie percentyli (Fan Charts)
    quantiles = [10, 25, 50, 75, 90]
    
    def calc_quantiles(arr_2d):
        return {f"p{q}": np.percentile(arr_2d, q, axis=0) for q in quantiles}
        
    # Odsetek trajektorii przekraczających próg krytyczny R_K >= 1.0 (empiryczne prawdopodobieństwo nadkrytyczności)
    empirical_rk_crit_med = np.mean(rk_med >= 1.0, axis=0)
    empirical_rk_crit_any = np.mean((rk_med >= 1.0) | (rk_high >= 1.0), axis=0)
    
    results = {
        "years": years,
        "n_samples": n_samples,
        "elapsed_seconds": elapsed,
        "empirical_criticality": {
            "medium": empirical_rk_crit_med,
            "any": empirical_rk_crit_any
        },
        "fan_charts": {
            "P_Kessler_any": calc_quantiles(p_kessler_any),
            "P_Kessler_low": calc_quantiles(p_kessler_low),
            "P_Kessler_medium": calc_quantiles(p_kessler_med),
            "P_Kessler_high": calc_quantiles(p_kessler_high),
            "P_Kessler_global": calc_quantiles(p_kessler_glob),
            "P_catastrophic_any": calc_quantiles(p_catastrophic_any),
            "R_K_medium": calc_quantiles(rk_med),
            "R_K_low": calc_quantiles(rk_low),
            "R_K_high": calc_quantiles(rk_high),
            "R_K_global": calc_quantiles(rk_glob),
            "N_total_medium": calc_quantiles(n_total_med),
            "N_total_global": calc_quantiles(n_total_glob)
        },
        "raw_terminal_df": pd.DataFrame(mc_params_list)
    }
    
    return results
