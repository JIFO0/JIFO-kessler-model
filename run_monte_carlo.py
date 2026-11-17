"""
Skrypt uruchomieniowy: Symulacja Monte Carlo, wykresy wachlarzowe (Fan Charts)
oraz dekompozycja wrażliwości i elastyczności.
"""

import os
import argparse
import json
import pandas as pd
from src.simulation import run_monte_carlo
from src.analysis import summarize_fan_chart_table, analyze_sensitivity
from src.visualization import plot_fan_charts, plot_sensitivity_tornado


def main():
    parser = argparse.ArgumentParser(description="Monte Carlo Kessler Hazard Simulator")
    parser.add_argument("--samples", type=int, default=2000, help="Liczba prób Monte Carlo (domyślnie 2000)")
    parser.add_argument("--seed", type=int, default=42, help="Ziarno losowości")
    args = parser.parse_args()

    print("=" * 75)
    print(f"   SYMULACJA MONTE CARLO KESSLERA - {args.samples:,} ŚCIEŻEK (2026-2126)")
    print("=" * 75)

    os.makedirs("results", exist_ok=True)

    # 1. Uruchomienie Monte Carlo
    print(f"\n[1/4] Uruchamianie silnika Monte Carlo ({args.samples:,} iteracji)...")
    mc_results = run_monte_carlo(n_samples=args.samples, start_year=2026, end_year=2126, dt=1.0, seed=args.seed)
    print(f"      Zakończono w {mc_results['elapsed_seconds']:.2f} s ({args.samples/mc_results['elapsed_seconds']:.1f} symulacji/s).")

    # 2. Tabele percentyli (Fan Chart summary)
    years = mc_results["years"]
    milestones = [2030, 2040, 2050, 2060, 2075, 2100, 2126]
    
    print("\n[2/4] WACHLARZ PRAWDOPODOBIEŃSTWA P(Kessler <= t) - DOWOLNA POWŁOKA (SYSTEMOWY):")
    table_any = summarize_fan_chart_table(mc_results["fan_charts"]["P_Kessler_any"], years, milestones)
    print(table_any.to_string(index=False))
    table_any.to_csv("results/fan_chart_system_table.csv", index=False)

    print("\n      WACHLARZ DLA PASA KRYTYCZNEGO: MODEL C - MEDIUM LEO (600–1100 km):")
    table_med = summarize_fan_chart_table(mc_results["fan_charts"]["P_Kessler_medium"], years, milestones)
    print(table_med.to_string(index=False))
    table_med.to_csv("results/fan_chart_medium_table.csv", index=False)

    # 3. Analiza wrażliwości
    print("\n[3/4] Dekompozycja wrażliwości (wpływ parametrów na prawdopodobieństwo kaskady w pasie MEDIUM LEO w 2100 r.):")
    sens_df = analyze_sensitivity(mc_results, target_col="P_Kessler_med_2100")
    print(sens_df.to_string(index=False))
    sens_df.to_csv("results/sensitivity_decomposition.csv", index=False)

    # 4. Generowanie wykresów
    print("\n[4/4] Generowanie wizualizacji...")
    plot_fan_charts(mc_results, output_path="results/fan_charts_probability.png")
    plot_sensitivity_tornado(sens_df, output_path="results/sensitivity_tornado.png")
    print("      [OK] Zapisano wykres wachlarzowy: results/fan_charts_probability.png")
    print("      [OK] Zapisano wykres tornado:     results/sensitivity_tornado.png")

    # Zapis metryk do JSON
    summary_data = {
        "n_samples": args.samples,
        "elapsed_seconds": mc_results["elapsed_seconds"],
        "system_prob_2050_median": float(mc_results["fan_charts"]["P_Kessler_any"]["p50"][int(len(years)*0.24)]),
        "system_prob_2100_median": float(mc_results["fan_charts"]["P_Kessler_any"]["p50"][int(len(years)*0.74)]),
        "sensitivity": sens_df.to_dict(orient="records")
    }
    with open("results/summary_metrics.json", "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 75)
    print("   SYMULACJA I ANALIZA ZAKOŃCZONE POMYŚLNIE!")
    print("=" * 75)


if __name__ == "__main__":
    main()
