"""
Implementacja 4 modeli dynamiki orbitalnej (Global, Low, Medium, High)
wraz ze sprzężonym systemem migracji i kalkulacją hazardu Kesslera.
Zgodna ze ścisłą mechaniką procesów gałązkowych (Branching Processes) i modelami NASA ODPO.
"""

import math
import numpy as np
from typing import Dict, Any, Tuple
from src.config import ShellParameters, SHELL_CONFIGS, MIGRATION_RATES, HAZARD_CONFIG, NON_LEO_BASELINE
from src.physics import (
    calculate_effective_volume,
    calculate_atmospheric_decay_time,
    calculate_collision_rate,
    calculate_logistic_launch,
    SECONDS_PER_YEAR
)


def _branching_escape_prob(rk: float, haz_mode: str = "smooth_branching") -> float:
    """
    Prawdopodobieństwo rozwinięcia samopodtrzymującej się kaskady Kesslera
    w procesie gałązkowym o liczbie reprodukcji R_K.
    """
    if haz_mode == "pure_branching":
        return (1.0 - 1.0 / rk) if rk > 1.0 else 0.0
    if rk <= 0.80:
        return 0.0
    if rk <= 1.05:
        return 0.05 * ((rk - 0.80) / 0.25) ** 2
    return 1.0 - 1.0 / rk


class OrbitalShellModel:
    """
    Model pojedynczej powłoki orbitalnej reprezentujący stan:
    X: aktywne satelity
    D10: obiekty nieaktywne / odłamki >10 cm
    D1: odłamki śmiertelne, niekatalogowane 1-10 cm
    D01: mikroodłamki erozyjne 1 mm - 1 cm
    """
    def __init__(self, params: ShellParameters):
        self.params = params
        self.V_eff = calculate_effective_volume(
            params.h_min_km, params.h_max_km, params.theta_eff
        )
        # Stan wyjściowy (dokładnie wg parametrów epoki t=0)
        self.X = float(params.X_0)
        self.D10 = float(params.D10_0)
        self.D1 = float(params.D1_0)
        self.D01 = float(params.D01_0)
        
        # Wskaźniki skumulowane (startują od 0 w roku początkowym)
        self.cumulative_hazard = 0.0
        self.cumulative_catastrophic = 0.0
        
    def reset(self):
        self.X = float(self.params.X_0)
        self.D10 = float(self.params.D10_0)
        self.D1 = float(self.params.D1_0)
        self.D01 = float(self.params.D01_0)
        self.cumulative_hazard = 0.0
        self.cumulative_catastrophic = 0.0

    def compute_step(self,
                     year: float,
                     dt: float,
                     migration_in_D10: float = 0.0,
                     migration_in_D1: float = 0.0,
                     migration_in_D01: float = 0.0,
                     n_substeps: int = 10) -> Dict[str, float]:
        """
        Krok całkowania czasowego dla powłoki.
        Zwraca stan na początku kroku (rok 'year') i całkowuje numerycznie do (year + dt)
        za pomocą podkroków, eliminując błąd przesunięcia fazowego (off-by-one).
        """
        p = self.params
        t_from_start = year - 2026.0
        
        # --- 1. Snapshot stanu i wskaźników chwilowych na początku roku 'year' ---
        x_snap = self.X
        d10_snap = self.D10
        d1_snap = self.D1
        d01_snap = self.D01
        p_kessler_snap = 1.0 - math.exp(-self.cumulative_hazard)
        p_catastrophic_snap = 1.0 - math.exp(-self.cumulative_catastrophic)
        
        # Czas rozpadu atmosferycznego na początku roku
        tau_decay_10 = calculate_atmospheric_decay_time(
            p.tau_decay_base, year, p.solar_cycle_amp
        )
        tau_decay_1 = max(0.5, tau_decay_10 * 0.7)
        tau_decay_01 = max(0.25, tau_decay_10 * 0.35)
        mu_10 = 1.0 / tau_decay_10
        mu_1 = 1.0 / tau_decay_1
        mu_01 = 1.0 / tau_decay_01
        
        # Kolizje chwilowe dla raportowania
        C_XX = calculate_collision_rate(
            self.X, self.X, p.sigma_XX_km2, p.v_rel_kms, self.V_eff,
            cam_efficiency=p.cam_eff_X_X, is_same_population=True
        )
        C_XD10 = calculate_collision_rate(
            self.X, self.D10, p.sigma_XD10_km2, p.v_rel_kms, self.V_eff,
            cam_efficiency=p.cam_eff_X_D10, is_same_population=False
        )
        C_XD1 = calculate_collision_rate(
            self.X, self.D1, p.sigma_XD1_km2, p.v_rel_kms, self.V_eff,
            cam_efficiency=p.cam_eff_X_D1, is_same_population=False
        )
        C_D10D10 = calculate_collision_rate(
            self.D10, self.D10, p.sigma_DD_km2, p.v_rel_kms, self.V_eff,
            cam_efficiency=p.cam_eff_D_D, is_same_population=True
        )
        C_D10D1 = calculate_collision_rate(
            self.D10, self.D1, p.sigma_DD_km2 * 0.6, p.v_rel_kms, self.V_eff,
            cam_efficiency=p.cam_eff_D_D, is_same_population=False
        )
        
        C_large = C_XX + C_XD10 + C_D10D10
        
        cap_factor = max(0.0, 1.0 - (self.D10 / p.D10_max_capacity))
        new_D10_sat = (2.0 * C_XX + C_XD10) * p.beta_10_sat * cap_factor
        new_D1_sat = (2.0 * C_XX + C_XD10) * p.beta_1_sat
        new_D10_dd = C_D10D10 * p.beta_10_dd * cap_factor
        new_D1_dd = C_D10D10 * p.beta_1_dd
        new_D10_pebble = C_XD1 * p.beta_10_pebble * cap_factor
        new_D1_pebble = (C_XD1 + C_D10D1) * p.beta_1_pebble
        
        new_D10_from_coll = new_D10_sat + new_D10_dd + new_D10_pebble
        new_D1_from_coll = new_D1_sat + new_D1_dd + new_D1_pebble
        new_D01_from_coll = ((2.0 * C_XX + C_XD10) * p.beta_01_sat +
                             C_D10D10 * p.beta_01_dd +
                             (C_XD1 + C_D10D1) * p.beta_01_pebble)
        
        decay_D10 = mu_10 * self.D10
        decay_D1 = mu_1 * self.D1
        decay_D01 = mu_01 * self.D01
        
        # Fizyczna liczba reprodukcji Kesslera R_K:
        # Zgodnie z teorią (docs/THEORY_AND_FORMULATIONS.md sekcja 7):
        # R_K = (tempo generowania nowych trwałych odłamków D10 ze zderzeń) / (tempo usuwania przez reentry)
        R_K = new_D10_from_coll / max(1e-6, decay_D10)
        
        # Obliczenie funkcji hazardu wejścia w kaskadę Kesslera:
        haz_mode = HAZARD_CONFIG.get("mode", "smooth_branching")
        escape_prob = _branching_escape_prob(R_K, haz_mode)
        hazard = C_large * escape_prob * HAZARD_CONFIG.get("scale_factor", 1.0)
            
        snapshot = {
            "year": year,
            "X": x_snap,
            "D10": d10_snap,
            "D1": d1_snap,
            "D01": d01_snap,
            "N_total": x_snap + d10_snap + d1_snap,
            "collisions_annual": C_large,
            "R_K": R_K,
            "hazard": hazard,
            "P_Kessler": p_kessler_snap,
            "P_catastrophic": p_catastrophic_snap,
            "decay_D10_out": decay_D10,
            "decay_D1_out": decay_D1,
            "decay_D01_out": decay_D01,
            "new_D10_from_coll": new_D10_from_coll,
            "new_D1_from_coll": new_D1_from_coll
        }
        
        # --- 2. Całkowanie numeryczne stanu z podkrokami (year -> year + dt) ---
        dsub = dt / float(n_substeps)
        mig_rate_10 = float(migration_in_D10)
        mig_rate_1 = float(migration_in_D1)
        mig_rate_01 = float(migration_in_D01)
        
        for s in range(n_substeps):
            y_sub = year + s * dsub
            t_sub = y_sub - 2026.0
            
            tau_10_s = calculate_atmospheric_decay_time(p.tau_decay_base, y_sub, p.solar_cycle_amp)
            tau_1_s = max(0.5, tau_10_s * 0.7)
            tau_01_s = max(0.25, tau_10_s * 0.35)
            mu_10_s = 1.0 / tau_10_s
            mu_1_s = 1.0 / tau_1_s
            mu_01_s = 1.0 / tau_01_s
            
            launch_s = calculate_logistic_launch(p.G_0, p.g_rate, p.K_launch, t_sub)
            decom_s = self.X / p.sat_lifetime
            act_to_deb_s = decom_s * (1.0 - p.q_pmd)
            
            c_xx_s = calculate_collision_rate(self.X, self.X, p.sigma_XX_km2, p.v_rel_kms, self.V_eff, p.cam_eff_X_X, True)
            c_xd10_s = calculate_collision_rate(self.X, self.D10, p.sigma_XD10_km2, p.v_rel_kms, self.V_eff, p.cam_eff_X_D10, False)
            c_xd1_s = calculate_collision_rate(self.X, self.D1, p.sigma_XD1_km2, p.v_rel_kms, self.V_eff, p.cam_eff_X_D1, False)
            c_xd01_s = calculate_collision_rate(self.X, self.D01, p.sigma_XD01_km2, p.v_rel_kms, self.V_eff, 0.0, False)
            c_dd_s = calculate_collision_rate(self.D10, self.D10, p.sigma_DD_km2, p.v_rel_kms, self.V_eff, p.cam_eff_D_D, True)
            c_d10d1_s = calculate_collision_rate(self.D10, self.D1, p.sigma_DD_km2 * 0.6, p.v_rel_kms, self.V_eff, p.cam_eff_D_D, False)
            
            c_large_s = c_xx_s + c_xd10_s + c_dd_s
            cap_s = max(0.0, 1.0 - (self.D10 / p.D10_max_capacity))
            
            new_10_s = ((2.0 * c_xx_s + c_xd10_s) * p.beta_10_sat + c_dd_s * p.beta_10_dd + c_xd1_s * p.beta_10_pebble) * cap_s
            new_1_s = (2.0 * c_xx_s + c_xd10_s) * p.beta_1_sat + c_dd_s * p.beta_1_dd + (c_xd1_s + c_d10d1_s) * p.beta_1_pebble
            new_01_s = (2.0 * c_xx_s + c_xd10_s) * p.beta_01_sat + c_dd_s * p.beta_01_dd + (c_xd1_s + c_d10d1_s) * p.beta_01_pebble
            
            decay_10_s = mu_10_s * self.D10
            decay_1_s = mu_1_s * self.D1
            decay_01_s = mu_01_s * self.D01
            
            # Chwilowy R_K w podkroku
            rk_s = new_10_s / max(1e-6, decay_10_s)
            esc_s = _branching_escape_prob(rk_s, haz_mode)
            h_s = c_large_s * esc_s * HAZARD_CONFIG.get("scale_factor", 1.0)
            
            self.cumulative_hazard += h_s * dsub
            self.cumulative_catastrophic += c_large_s * dsub
            
            # Równania bilansu populacji
            sat_loss_large_s = 2.0 * c_xx_s + c_xd10_s
            sat_loss_pebble_s = c_xd1_s + c_xd01_s * p.p_kill_01
            
            dx_s = launch_s - decom_s - (sat_loss_large_s + sat_loss_pebble_s)
            dd10_s = (act_to_deb_s + sat_loss_pebble_s + new_10_s - decay_10_s 
                      + mig_rate_10 - (2.0 * c_dd_s + c_xd10_s))
            dd1_s = new_1_s - decay_1_s + mig_rate_1 - (c_xd1_s + c_d10d1_s)
            dd01_s = new_01_s - decay_01_s + mig_rate_01
            
            self.X = max(0.0, self.X + dx_s * dsub)
            self.D10 = max(0.0, min(p.D10_max_capacity, self.D10 + dd10_s * dsub))
            self.D1 = max(0.0, self.D1 + dd1_s * dsub)
            self.D01 = max(0.0, self.D01 + dd01_s * dsub)
            
        return snapshot


class CoupledOrbitalSystem:
    """
    Sprzężony system orbitalny modelujący warstwy:
    LOW (200-600 km), MEDIUM (600-1100 km), HIGH (1100-2000 km)
    oraz spójny, zagregowany model GLOBAL (LEO + MEO/GEO).
    Uwzględnia fizyczny przepływ tranzytowy odłamków opadających między warstwami.
    """
    def __init__(self, custom_configs: Dict[str, ShellParameters] = None):
        configs = custom_configs or SHELL_CONFIGS
        self.configs = configs
        self.models = {
            "low": OrbitalShellModel(configs["low"]),
            "medium": OrbitalShellModel(configs["medium"]),
            "high": OrbitalShellModel(configs["high"]),
            "global": OrbitalShellModel(configs["global"])
        }
        self.non_leo_X = NON_LEO_BASELINE["X"]
        self.non_leo_D10 = NON_LEO_BASELINE["D10"]
        self.non_leo_D1 = NON_LEO_BASELINE["D1"]
        self.non_leo_D01 = NON_LEO_BASELINE.get("D01", 50000000.0)
        
    def reset(self):
        for model in self.models.values():
            model.reset()
            
    def step(self, year: float, dt: float) -> Dict[str, Any]:
        """
        Wykonuje sprzężony krok symulacji dla wszystkich modeli.
        Odłamki opadające z HIGH wkraczają do MEDIUM.
        Odłamki opadające z MEDIUM wkraczają do LOW.
        Model GLOBAL stanowi ścisłą, niesprzeczną sumę powłok LEO oraz bazy non-LEO.
        """
        # 1. Krok dla warstwy HIGH
        res_high = self.models["high"].compute_step(year, dt, migration_in_D10=0.0, migration_in_D1=0.0, migration_in_D01=0.0)
        
        # Migracja z HIGH do MEDIUM (ułamek opadających obiektów)
        h2m_rate = MIGRATION_RATES.get("high_to_medium", 0.90)
        mig_h2m_10 = res_high["decay_D10_out"] * h2m_rate
        mig_h2m_1 = res_high["decay_D1_out"] * h2m_rate
        mig_h2m_01 = res_high["decay_D01_out"] * h2m_rate
        
        # 2. Krok dla warstwy MEDIUM (przyjmuje odłamki z HIGH)
        res_med = self.models["medium"].compute_step(year, dt, migration_in_D10=mig_h2m_10, migration_in_D1=mig_h2m_1, migration_in_D01=mig_h2m_01)
        
        # Migracja z MEDIUM do LOW (odłamki wkraczające w gęstszą termosferę)
        m2l_rate = MIGRATION_RATES.get("medium_to_low", 0.95)
        mig_m2l_10 = res_med["decay_D10_out"] * m2l_rate
        mig_m2l_1 = res_med["decay_D1_out"] * m2l_rate
        mig_m2l_01 = res_med["decay_D01_out"] * m2l_rate
        
        # 3. Krok dla warstwy LOW (przyjmuje odłamki z MEDIUM i spala je ostatecznie)
        res_low = self.models["low"].compute_step(year, dt, migration_in_D10=mig_m2l_10, migration_in_D1=mig_m2l_1, migration_in_D01=mig_m2l_01)
        
        # 4. Prawdopodobieństwo systemowe Kesslera (wejście w kaskadę w przynajmniej jednej powłoce LEO)
        p_safe_kessler = ((1.0 - res_low["P_Kessler"]) * 
                          (1.0 - res_med["P_Kessler"]) * 
                          (1.0 - res_high["P_Kessler"]))
        P_Kessler_any = 1.0 - p_safe_kessler
        
        # Prawdopodobieństwo katastroficznego zderzenia w LEO
        p_safe_coll = ((1.0 - res_low["P_catastrophic"]) * 
                       (1.0 - res_med["P_catastrophic"]) * 
                       (1.0 - res_high["P_catastrophic"]))
        P_catastrophic_any = 1.0 - p_safe_coll
        
        # 5. Agregacja dla modelu GLOBAL
        tot_new_10 = res_low["new_D10_from_coll"] + res_med["new_D10_from_coll"] + res_high["new_D10_from_coll"]
        tot_decay_10 = res_low["decay_D10_out"] + res_med["decay_D10_out"] + res_high["decay_D10_out"]
        global_rk = tot_new_10 / max(1e-4, tot_decay_10)
        
        res_glob = {
            "year": year,
            "X": res_low["X"] + res_med["X"] + res_high["X"] + self.non_leo_X,
            "D10": res_low["D10"] + res_med["D10"] + res_high["D10"] + self.non_leo_D10,
            "D1": res_low["D1"] + res_med["D1"] + res_high["D1"] + self.non_leo_D1,
            "D01": res_low["D01"] + res_med["D01"] + res_high["D01"] + self.non_leo_D01,
            "N_total": (res_low["N_total"] + res_med["N_total"] + res_high["N_total"] + 
                        self.non_leo_X + self.non_leo_D10 + self.non_leo_D1),
            "collisions_annual": (res_low["collisions_annual"] + 
                                  res_med["collisions_annual"] + 
                                  res_high["collisions_annual"]),
            "R_K": global_rk,
            "hazard": max(res_low["hazard"], res_med["hazard"], res_high["hazard"]),
            "P_Kessler": P_Kessler_any,
            "P_catastrophic": P_catastrophic_any,
            "decay_D10_out": tot_decay_10,
            "decay_D1_out": res_low["decay_D1_out"] + res_med["decay_D1_out"] + res_high["decay_D1_out"]
        }
        
        return {
            "year": year,
            "low": res_low,
            "medium": res_med,
            "high": res_high,
            "global": res_glob,
            "P_Kessler_any": P_Kessler_any,
            "P_catastrophic_any": P_catastrophic_any
        }
