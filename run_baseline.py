"""
Skrypt uruchomieniowy: Symulacja bazowa (deterministyczna) i scenariusze regulacyjne.
"""

import os
import pandas as pd
from src.simulation import run_deterministic
from src.analysis import compute_policy_scenarios
from src.visualization import plot_reproduction_dynamics


def main():
    print("=" * 70)
    print("   MODEL SYNDROMU KESSLERA - SYMULACJA BAZOWA DETERMINISTYCZNA (2026-2126)")
    print("=" * 70)
    
    # 1. Uruchomienie symulacji bazowej
    df_base = run_deterministic(start_year=2026, end_year=2126, dt=1.0)
    
    os.makedirs("results", exist_ok=True)
    df_base.to_csv("results/baseline_trajectory.csv", index=False)
    print("\n[OK] Zapisano trajektorię bazową do: results/baseline_trajectory.csv")
    
    # 2. Wyświetlenie kluczowych punktów czasowych
    milestones = [2026, 2035, 2050, 2075, 2100, 2126]
    display_cols = ["year", "medium_R_K", "high_R_K", "low_R_K", "global_R_K", 
                    "medium_P_Kessler", "P_Kessler_any", "medium_N_total"]
    
    sub_df = df_base[df_base["year"].isin(milestones)][display_cols]
    print("\n--- KLUCZOWE WSKAŹNIKI W TRAJEKTORII BAZOWEJ ---")
    print(sub_df.to_string(index=False))
    
    # 3. Wygenerowanie wykresu R_K(t)
    plot_reproduction_dynamics(df_base, output_path="results/reproduction_numbers_rk.png")
    print("\n[OK] Wygenerowano wykres współczynnika reprodukcji R_K: results/reproduction_numbers_rk.png")
    
    # 4. Scenariusze polityki orbitalnej
    print("\n--- ANALIZA SCENARIUSZY POLITYKI ORBITALNEJ (Stan w 2100 r.) ---")
    scenarios = compute_policy_scenarios(df_base)
    for s_name, s_df in scenarios.items():
        row_2100 = s_df[s_df["year"] == 2100].iloc[0]
        print(f"Scenariusz: {s_name:25} | P(Kessler_any <= 2100) = {row_2100['P_Kessler_any']*100:5.1f}% | R_K(med) = {row_2100['medium_R_K']:5.2f}")
        
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
