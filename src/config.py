"""
Konfiguracja parametrów fizycznych, orbitalnych i ekonometrycznych dla modeli Kesslera.
Dane bazowe skalibrowane wg ESA MASTER-8 (luty 2026), NASA ODPO oraz modeli literatury (Rao & Rondina 2025).
"""

from dataclasses import dataclass, field
from typing import Dict, Any

EARTH_RADIUS_KM = 6378.137

# Składniki wyjściowe dla obiektów poza LEO (MEO/GEO), stan 2026 r.
NON_LEO_BASELINE = {
    "X": 300.0,         # Satelity geostacjonarne i nawigacyjne (GEO/MEO)
    "D10": 28650.0,     # Obiekty martwe i stopnie rakiet w GEO/GTO/MEO
    "D1": 500000.0,     # Odłamki 1-10 cm poza LEO
    "D01": 50000000.0   # Mikroodłamki 1 mm - 1 cm poza LEO
}

@dataclass
class ShellParameters:
    name: str
    h_min_km: float
    h_max_km: float
    
    # Stan wyjściowy (rok 2026)
    X_0: float          # Aktywne satelity
    D10_0: float        # Odłamki i martwe obiekty >10 cm
    D1_0: float         # Odłamki 1-10 cm (śmiertelne, niekatalogowane)
    D01_0: float        # Mikroodłamki erozyjne 1 mm - 1 cm (ESA MASTER-8)
    
    # Parametry przepływu i ekonomii startów
    G_0: float          # Początkowa roczna liczba wynoszonych satelitów (satelity/rok)
    g_rate: float       # Roczna stopa wzrostu startów (0.01 - 0.10)
    K_launch: float     # Maksymalna pojemność rynkowa (nasycenie logistyczne)
    q_pmd: float        # Skuteczność usuwania po misji (PMD compliance rate, 0-1)
    sat_lifetime: float # Czas operacyjny satelity (lata)
    
    # Fizyka orbitalna
    tau_decay_base: float # Bazowy czas naturalnego opadania w atmosferze (lata)
    theta_eff: float      # Współczynnik koncentracji przestrzennej (anizotropia)
    v_rel_kms: float      # Średnia prędkość względna (km/s)
    
    # Efektywność unikania kolizji (CAM)
    cam_eff_X_X: float = 0.999   # Aktywny vs Aktywny
    cam_eff_X_D10: float = 0.98  # Aktywny vs Duży katalogowany
    cam_eff_X_D1: float = 0.0    # Aktywny vs Niekatalogowany 1-10 cm (satelita ślepy!)
    cam_eff_D_D: float = 0.0     # Pasywny vs Pasywny

    # Średnie przekroje kolizyjne (km^2)
    sigma_XX_km2: float = 6.0e-6     # 6 m^2 (efektywny przekrój paneli i korpusu)
    sigma_XD10_km2: float = 4.0e-6   # 4 m^2 (efektywny przekrój zderzenia satelita vs duży wrak/stopień)
    sigma_XD1_km2: float = 0.50e-6   # 0.5 m^2 (wrażliwy korpus)
    sigma_DD_km2: float = 0.20e-6    # 0.2 m^2 (średnia dla zderzeń wraków >10 cm, w tym stopni rakiet)

    # Liczba odłamków przy zderzeniu katastroficznym z satelitą (NASA SSBM)
    beta_10_sat: float = 650.0
    beta_1_sat: float = 32000.0
    beta_01_sat: float = 1600000.0
    
    # Liczba odłamków przy zderzeniu dwóch odłamków D10 x D10
    beta_10_dd: float = 120.0
    beta_1_dd: float = 6000.0
    beta_01_dd: float = 300000.0
    
    # Liczba odłamków przy uderzeniu punktowym 1-10 cm w satelitę (częściowy rozpad/erozja)
    beta_10_pebble: float = 5.0
    beta_1_pebble: float = 250.0
    beta_01_pebble: float = 12500.0
    
    # Przekrój i prawdopodobieństwo awarii krytycznej przy trafieniu mikroodłamkiem 1 mm - 1 cm
    sigma_XD01_km2: float = 0.25e-6
    p_kill_01: float = 0.015
    
    # Fizyczna pojemność masowa powłoki
    D10_max_capacity: float = 2.0e6
    
    # Amplituda modulacji cyklem słonecznym (11 lat)
    solar_cycle_amp: float = 0.0


# Definicje 4 modeli bazowych (zbilansowane wg rzeczywistej alokacji startów i fizyki)
SHELL_CONFIGS: Dict[str, ShellParameters] = {
    # Model B: LOW LEO (200 - 600 km) - Główny rejon megakonstelacji (Starlink, Kuiper, Qianfan)
    "low": ShellParameters(
        name="Model B (LOW: 200-600 km)",
        h_min_km=200.0,
        h_max_km=600.0,
        X_0=7800.0,
        D10_0=5200.0,
        D1_0=250000.0,
        D01_0=30000000.0,
        G_0=3200.0,                # ~90% światowych startów trafia poniżej 600 km
        g_rate=0.05,
        K_launch=12000.0,          # Stan nasycenia: 12000 * 5 = ~60k aktywnych satelitów
        q_pmd=0.96,                # Bardzo wysoka dyscyplina i krótki czas naturalnego opadania
        sat_lifetime=5.0,
        tau_decay_base=4.0,        # 4 lata bazowego czasu opadania
        theta_eff=0.15,            # Koncentracja wokół 53° i 550 km
        v_rel_kms=10.5,
        cam_eff_X_D10=0.98,
        solar_cycle_amp=0.55,      # Bardzo silny wpływ cyklu słonecznego
        D10_max_capacity=1.5e6
    ),
    
    # Model C: MEDIUM LEO (600 - 1100 km) - Pas SSO i starych odłamków (Fengyun, Cosmos-Iridium)
    # Brak megakonstelacji ze względu na restrykcje FCC/ESA i brak szybkiej deorbitacji
    "medium": ShellParameters(
        name="Model C (MEDIUM: 600-1100 km)",
        h_min_km=600.0,
        h_max_km=1100.0,
        X_0=2200.0,
        D10_0=14800.0,             # Największa populacja starych odłamków
        D1_0=550000.0,
        D01_0=110000000.0,
        G_0=280.0,                 # Realistyczny umiarkowany ruch (teledetekcja, nauka, SSO)
        g_rate=0.02,
        K_launch=600.0,            # Stabilizacja wokół ~4000 satelitów (600 * 7 = 4200)
        q_pmd=0.90,
        sat_lifetime=7.0,
        tau_decay_base=85.0,       # Prawie stulecie retencji
        theta_eff=0.18,            # Skupienie polarne SSO 98°
        v_rel_kms=12.2,
        cam_eff_X_D10=0.95,
        solar_cycle_amp=0.20,
        D10_max_capacity=2.5e6
    ),
    
    # Model D: HIGH LEO (1100 - 2000 km) - Rejon radzieckich stopni SL-8/SL-16
    # Znikomy ruch komercyjny ze względu na wewnętrzny pas radiacyjny Van Allena
    "high": ShellParameters(
        name="Model D (HIGH: 1100-2000 km)",
        h_min_km=1100.0,
        h_max_km=2000.0,
        X_0=1000.0,
        D10_0=8500.0,              # Radzieckie stopnie SL-8/SL-16 o dużej masie
        D1_0=200000.0,
        D01_0=40000000.0,
        G_0=40.0,                  # Znikoma liczba nowych misji
        g_rate=0.01,
        K_launch=80.0,             # Stabilizacja wokół ~800 satelitów (80 * 10 = 800)
        q_pmd=0.85,
        sat_lifetime=10.0,
        tau_decay_base=1200.0,     # Ponad tysiąc lat retencji
        theta_eff=0.25,
        v_rel_kms=13.5,
        cam_eff_X_D10=0.90,
        solar_cycle_amp=0.02,
        D10_max_capacity=3.0e6
    ),
    
    # Model A: GLOBAL (200 - 50 000 km) - Reprezentacja zagregowana
    "global": ShellParameters(
        name="Model A (GLOBAL: Zagregowany LEO + GEO)",
        h_min_km=200.0,
        h_max_km=50000.0,
        X_0=11300.0,               # 7800 (low) + 2200 (med) + 1000 (high) + 300 (non-leo)
        D10_0=57150.0,             # 5200 + 14800 + 8500 + 28650
        D1_0=1500000.0,            # 250k + 550k + 200k + 500k
        D01_0=230000000.0,         # 30M + 110M + 40M + 50M
        G_0=3520.0,
        g_rate=0.045,
        K_launch=12680.0,
        q_pmd=0.95,
        sat_lifetime=5.5,
        tau_decay_base=50.0,
        theta_eff=0.05,
        v_rel_kms=11.0,
        cam_eff_X_D10=0.96,
        solar_cycle_amp=0.35,
        D10_max_capacity=1.0e7
    )
}

# Macierz migracji tranzytowej (ułamek obiektów opadających z warstwy wyższej do niższej)
MIGRATION_RATES = {
    "high_to_medium": 0.90,   # Ułamek opadających obiektów z High wkraczających do Medium
    "medium_to_low": 0.95,    # Ułamek opadających obiektów z Medium wkraczających do Low
}

# Konfiguracja funkcji hazardu kaskady Kesslera:
# Domyślnie "smooth_branching" łączy częstość zderzeń katastroficznych C_large
# z prawdopodobieństwem rozwinięcia samonapędzającej się kaskady f(R_K)
# w oparciu o procesy gałązkowe z gładkim przejściem wokół progu krytycznego R_K = 1.0:
# h(t) = C_catastrophic(t) / (1 + exp(-alpha * (R_K(t) - 1.0)))
HAZARD_CONFIG = {
    "mode": "smooth_branching",  # "smooth_branching" (zalecane) lub "pure_branching"
    "sigmoid_alpha": 4.0,        # Czułość przejścia wokół progu krytycznego R_K = 1.0
    "scale_factor": 1.0,
}

# Ustawienia horyzontu czasowego
SIMULATION_CONFIG = {
    "start_year": 2026,
    "end_year": 2126,
    "dt": 1.0,          # Krok raportowania (lata)
    "sub_steps": 10     # Podkroki całkowania (dt = 0.1 roku) dla stabilności numerycznej
}

# Predefiniowane scenariusze rynkowe i regulacyjne (Presets)
PRESETS = {
    "realistic_2026": {
        "name": "Realistyczny 2026–2035 (Starlink Gen2 + Kuiper + Qianfan + Guowang)",
        "description": "Najbardziej realistyczna trajektoria oparta na zgłoszeniach ITU i harmonogramach konstelacji: ponad 11k Starlinków, start Kuipera i chińskich konstelacji (Qianfan/Guowang), koncentracja >90% startów w Low LEO (<600 km), wysoka deorbitacja (Starlink 5-letnia reguła), stabilizacja wokół 65k aktywnych satelitów.",
        "params": {
            "g_multiplier": 1.2,          # Umiarkowane przyspieszenie megakonstelacji
            "pmd_shift": 0.01,            # Wysoka deorbitacja w Low LEO (97%)
            "beta_multiplier": 1.0,       # Standardowa fragmentacja NASA SSBM
            "cam_eff_shift": 0.0,
            "sat_lifetime": 5.0
        }
    },
    "starship_expansion": {
        "name": "Ekspansja Starship / Tani Dostęp (Wysoki wzrost, niższy PMD)",
        "description": "Scenariusz skrajnego spadku kosztów wyniesienia na orbitę (poniżej $200/kg). Ogromny napływ komercyjnych satelitów przy częściowym spadku dyscypliny deorbitacji (PMD ~85%) i wzroście odłamków.",
        "params": {
            "g_multiplier": 2.2,
            "pmd_shift": -0.08,
            "beta_multiplier": 1.15,
            "cam_eff_shift": -0.03,
            "sat_lifetime": 4.5
        }
    },
    "zero_debris_strict": {
        "name": "Karta Zero Debris ESA & Reguła 5-lat FCC (98% PMD)",
        "description": "Ścisła międzynarodowa koordynacja: obowiązkowa deorbitacja w ciągu maksymalnie 5 lat, 98% skuteczności PMD, aktywne usuwanie wraków (ADR), spowolnienie niekontrolowanych startów.",
        "params": {
            "g_multiplier": 0.7,
            "pmd_shift": 0.04,
            "beta_multiplier": 0.85,
            "cam_eff_shift": 0.02,
            "sat_lifetime": 6.0
        }
    },
    "conservative_legacy": {
        "name": "Konserwatywny / Historyczny (Spowolnienie megakonstelacji)",
        "description": "Scenariusz wolnego wzrostu odpowiadający umiarkowanej dynamice, bez eskalacji dziesiątek tysięcy nowych satelitów rocznie.",
        "params": {
            "g_multiplier": 0.4,
            "pmd_shift": 0.0,
            "beta_multiplier": 1.0,
            "cam_eff_shift": 0.0,
            "sat_lifetime": 5.5
        }
    }
}


def create_custom_configs(g_multiplier: float = 1.0,
                          pmd_shift: float = 0.0,
                          beta_multiplier: float = 1.0,
                          cam_eff_shift: float = 0.0,
                          sat_lifetime_override: float = None) -> Dict[str, ShellParameters]:
    """
    Tworzy zmodyfikowaną konfigurację 4 modeli na podstawie suwaków/parametrów użytkownika.
    """
    import copy
    cfgs = copy.deepcopy(SHELL_CONFIGS)
    
    for key, p in cfgs.items():
        # Skalowanie wzrostu startów
        p.g_rate = max(0.005, min(0.20, p.g_rate * g_multiplier))
        p.K_launch = p.K_launch * max(0.5, min(4.0, g_multiplier))
        
        # Skalowanie deorbitacji PMD
        p.q_pmd = max(0.50, min(0.999, p.q_pmd + pmd_shift))
        
        # Skalowanie fragmentacji
        p.beta_10_sat = p.beta_10_sat * beta_multiplier
        p.beta_1_sat = p.beta_1_sat * beta_multiplier
        p.beta_01_sat = p.beta_01_sat * beta_multiplier
        p.beta_10_dd = p.beta_10_dd * beta_multiplier
        p.beta_1_dd = p.beta_1_dd * beta_multiplier
        p.beta_01_dd = p.beta_01_dd * beta_multiplier
        p.beta_10_pebble = p.beta_10_pebble * beta_multiplier
        p.beta_1_pebble = p.beta_1_pebble * beta_multiplier
        p.beta_01_pebble = p.beta_01_pebble * beta_multiplier
        
        # Skalowanie skuteczności CAM
        p.cam_eff_X_D10 = max(0.70, min(0.999, p.cam_eff_X_D10 + cam_eff_shift))
        
        if sat_lifetime_override is not None:
            if key == "low":
                p.sat_lifetime = max(1.0, min(15.0, sat_lifetime_override))
            else:
                p.sat_lifetime = max(1.0, min(15.0, p.sat_lifetime * (sat_lifetime_override / 5.0)))
            
    return cfgs
