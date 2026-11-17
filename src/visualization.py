"""
Moduł wizualizacji: generowanie wykresów wachlarzowych (fan charts),
trajektorii reprodukcji R_K, dynamiki populacji oraz dekompozycji wrażliwości.
"""

import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Dict, Any


def setup_plot_style():
    """Ustawia estetyczny i czytelny styl wykresów."""
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    plt.rcParams.update({
        'font.size': 11,
        'axes.labelsize': 12,
        'axes.titlesize': 14,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'figure.titlesize': 16,
        'figure.dpi': 150
    })


def plot_fan_charts(mc_results: Dict[str, Any], output_path: str = "results/fan_charts_probability.png"):
    """
    Rysuje wykresy wachlarzowe prawdopodobieństwa Kesslera P(K <= t)
    dla modelu systemowego (Any shell) oraz poszczególnych warstw.
    """
    setup_plot_style()
    years = mc_results["years"]
    fan = mc_results["fan_charts"]
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10), sharey=True)
    
    configs = [
        (axes[0, 0], "P_Kessler_any", "Prawdopodobieństwo Systemowe (Dowolna powłoka)", "#d62728"),
        (axes[0, 1], "P_Kessler_medium", "Model C: MEDIUM LEO (600–1100 km) [Krytyczny]", "#ff7f0e"),
        (axes[1, 0], "P_Kessler_high", "Model D: HIGH LEO (1100–2000 km)", "#9467bd"),
        (axes[1, 1], "P_Kessler_low", "Model B: LOW LEO (200–600 km)", "#2ca02c")
    ]
    
    for ax, key, title, color in configs:
        data = fan[key]
        p10 = data["p10"]
        p25 = data["p25"]
        p50 = data["p50"]
        p75 = data["p75"]
        p90 = data["p90"]
        
        # Cieniowanie przedziałów ufności
        ax.fill_between(years, p10, p90, color=color, alpha=0.15, label="Przedział 10%–90%")
        ax.fill_between(years, p25, p75, color=color, alpha=0.30, label="Przedział 25%–75%")
        ax.plot(years, p50, color=color, lw=2.5, label="Mediana (50%)")
        
        ax.set_title(title, fontweight='bold')
        ax.set_xlabel("Rok")
        ax.set_ylabel("P(Kessler ≤ t)")
        ax.set_ylim(-0.02, 1.02)
        ax.axhline(0.5, color='gray', linestyle=':', alpha=0.6)
        ax.legend(loc="upper left", frameon=True)
        ax.grid(True, linestyle="--", alpha=0.5)
        
    plt.suptitle("Wachlarz Prawdopodobieństwa Syndromu Kesslera (2026–2126) [Monte Carlo]", fontsize=16, y=0.98)
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()


def plot_reproduction_dynamics(base_df: pd.DataFrame, output_path: str = "results/reproduction_numbers_rk.png"):
    """
    Rysuje trajektorie współczynnika reprodukcji R_K(t) dla 4 modeli z zaznaczonym progiem krytycznym R_K = 1.
    """
    setup_plot_style()
    plt.figure(figsize=(12, 7))
    
    years = base_df["year"]
    
    plt.plot(years, base_df["medium_R_K"], label="MEDIUM LEO (600–1100 km) [Zapalnik]", color="#d62728", lw=3.0)
    plt.plot(years, base_df["high_R_K"], label="HIGH LEO (1100–2000 km)", color="#ff7f0e", lw=2.2)
    plt.plot(years, base_df["global_R_K"], label="GLOBAL (Zagregowany 200–50k km)", color="#1f77b4", lw=2.0, linestyle="--")
    plt.plot(years, base_df["low_R_K"], label="LOW LEO (200–600 km) [Bufor atmosfery]", color="#2ca02c", lw=2.2)
    
    # Próg krytyczny R_K = 1
    plt.axhline(1.0, color='black', linestyle='--', lw=2.0, label="Próg Krytyczny R_K = 1.0 (Criticality)")
    
    plt.axhspan(1.0, 10.0, color='red', alpha=0.08, label="Strefa Samopodtrzymującego Runaway")
    plt.axhspan(0.0, 1.0, color='green', alpha=0.06, label="Strefa Stabilna (Oczyszczanie dominujące)")
    
    plt.title("Ewolucja Współczynnika Reprodukcji Kesslera $R_K(t)$ (2026–2126)", fontsize=15, fontweight='bold')
    plt.xlabel("Rok", fontsize=12)
    plt.ylabel("Współczynnik Reprodukcji $R_K$", fontsize=12)
    plt.yscale("log")
    plt.ylim(0.01, 10.0)
    plt.legend(loc="upper left", frameon=True)
    plt.grid(True, which="both", linestyle="--", alpha=0.5)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()


def plot_sensitivity_tornado(sens_df: pd.DataFrame, output_path: str = "results/sensitivity_tornado.png"):
    """
    Rysuje wykres tornado standaryzowanych wpływów parametrów na ryzyko kaskady Kesslera.
    """
    setup_plot_style()
    plt.figure(figsize=(10, 6))
    
    params = sens_df["Parametr"]
    betas = sens_df["Standaryzowany Wpływ (Beta)"]
    colors = ['#d62728' if b > 0 else '#2ca02c' for b in betas]
    
    y_pos = np.arange(len(params))
    plt.barh(y_pos, betas, color=colors, alpha=0.85, edgecolor='black')
    plt.yticks(y_pos, params)
    plt.axvline(0, color='black', lw=1.2)
    
    plt.title("Dekompozycja Wrażliwości: Wpływ Parametrów na Ryzyko Kesslera w 2100 r.", fontsize=14, fontweight='bold')
    plt.xlabel("Standaryzowany współczynnik wpływu (Beta OLS)", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.5)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
