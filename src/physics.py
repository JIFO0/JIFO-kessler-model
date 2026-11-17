"""
Moduł fizyki orbitalnej: obliczenia objętości, kinetyki zderzeń,
rozpadu NASA SSBM oraz tłumienia atmosferycznego z cyklem słonecznym.
"""

import math
import numpy as np
from typing import Tuple
from src.config import EARTH_RADIUS_KM

SECONDS_PER_YEAR = 365.25 * 86400.0  # 31,557,600 sekund


def calculate_shell_volume(h_min_km: float, h_max_km: float) -> float:
    """
    Oblicza geometryczną objętość powłoki sferycznej wokół Ziemi w km^3.
    """
    r1 = EARTH_RADIUS_KM + h_min_km
    r2 = EARTH_RADIUS_KM + h_max_km
    return (4.0 / 3.0) * math.pi * (r2**3 - r1**3)


def calculate_effective_volume(h_min_km: float, h_max_km: float, theta: float) -> float:
    """
    Oblicza efektywną objętość roboczą (uwzględniając skupienie inklinacyjne/anizotropię).
    V_eff = V_shell * theta
    """
    v_shell = calculate_shell_volume(h_min_km, h_max_km)
    return v_shell * max(1e-5, min(1.0, theta))


def calculate_atmospheric_decay_time(tau_base_years: float,
                                     year: float,
                                     solar_amp: float = 0.0,
                                     solar_cycle_period: float = 11.0,
                                     solar_peak_year: float = 2025.5) -> float:
    """
    Oblicza chwilowy czas życia obiektu (tau_decay) z uwzględnieniem 11-letniego cyklu słonecznego.
    W maksimum słonecznym opór atmosferyczny wzrasta, więc tau maleje (krótszy czas retencji).
    """
    if solar_amp <= 0.0:
        return tau_base_years
    
    # Przesunięcie fazowe: w maksimum słonecznym (solar_peak) atmosfera puchnie -> tau spada
    # tau(t) = tau_base / (1 + amp * cos(2*pi*(t - peak)/11))
    phase = 2.0 * math.pi * (year - solar_peak_year) / solar_cycle_period
    factor = 1.0 + solar_amp * math.cos(phase)
    # Zabezpieczenie przed dzieleniem przez zero
    factor = max(0.1, factor)
    return tau_base_years / factor


def nasa_breakup_fragments(mass_kg: float = 1200.0,
                           min_size_m: float = 0.1) -> float:
    """
    NASA Standard Satellite Breakup Model (SSBM) dla katastroficznego zderzenia:
    N(Lc >= min_size) = 0.1 * (M_total)^0.75 * Lc^(-1.71)
    """
    return 0.1 * (mass_kg ** 0.75) * (min_size_m ** -1.71)


def calculate_collision_rate(N_A: float,
                             N_B: float,
                             sigma_km2: float,
                             v_rel_kms: float,
                             V_eff_km3: float,
                             cam_efficiency: float = 0.0,
                             is_same_population: bool = False) -> float:
    """
    Oblicza roczną liczbę kolizji pomiędzy dwoma populacjami obiektów w powłoce.
    C = (pairs * sigma * v_annual / V_eff) * (1 - CAM)
    """
    if N_A <= 0 or N_B <= 0 or V_eff_km3 <= 0:
        return 0.0
    
    # Liczba par
    if is_same_population:
        pairs = 0.5 * N_A * (N_A - 1.0) if N_A > 1 else 0.0
    else:
        pairs = N_A * N_B
        
    v_annual_km = v_rel_kms * SECONDS_PER_YEAR
    swept_rate_per_pair = (sigma_km2 * v_annual_km) / V_eff_km3
    
    raw_rate = pairs * swept_rate_per_pair
    # Redukcja przez aktywne manewry unikania
    effective_rate = raw_rate * (1.0 - max(0.0, min(1.0, cam_efficiency)))
    return max(0.0, effective_rate)


def calculate_reproduction_number(beta: float,
                                  annual_coll_rate: float,
                                  total_objects: float,
                                  tau_decay_years: float) -> float:
    """
    Oblicza wskaźnik reprodukcji śmieci Kesslera:
    R_K = beta * P_coll_per_object * tau_decay
    gdzie P_coll_per_object = annual_coll_rate / total_objects
    """
    if total_objects <= 0 or tau_decay_years <= 0:
        return 0.0
    
    p_coll_per_obj = annual_coll_rate / total_objects
    return beta * p_coll_per_obj * tau_decay_years


def calculate_logistic_launch(G_0: float,
                              g_rate: float,
                              K_launch: float,
                              dt_years: float) -> float:
    """
    Model logistycznego wzrostu liczby wynoszonych satelitów (launch rate).
    G(t) = K / (1 + ((K - G0)/G0) * exp(-g * t))
    """
    if G_0 <= 0:
        return 0.0
    if K_launch <= G_0:
        return K_launch
        
    ratio = (K_launch - G_0) / G_0
    exp_factor = math.exp(-g_rate * dt_years)
    return K_launch / (1.0 + ratio * exp_factor)
