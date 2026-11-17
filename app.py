"""
Aplikacja Webowa Flask do Interaktywnej Analizy Modeli Kesslera w Przeglądarce.
Umożliwia sterowanie parametrami bazowymi, wybór presetów (np. Starlink Gen2 + Kuiper + Qianfan)
oraz generowanie wykresów i tabel prawdopodobieństwa w %.
"""

import os
import json
import urllib.request
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, jsonify

from src.config import (
    SHELL_CONFIGS, PRESETS, create_custom_configs, SIMULATION_CONFIG
)
from src.simulation import run_deterministic, run_monte_carlo
from src.analysis import summarize_fan_chart_table, analyze_sensitivity

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.route("/")
def index():
    return render_template("index.html", presets=PRESETS)


@app.route("/zrodla")
def sources():
    return render_template("sources.html")


@app.route("/api/feedback", methods=["POST"])
def submit_feedback():
    try:
        data = request.get_json() or {}
        author = str(data.get("author", "")).strip() or "Anonim"
        category = str(data.get("category", "Opinia")).strip()
        message = str(data.get("message", "")).strip()

        if not message or len(message) < 3:
            return jsonify({"error": "Wiadomość musi mieć co najmniej 3 znaki."}), 400

        webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
        timestamp = datetime.now(timezone.utc).isoformat()

        entry = {
            "timestamp": timestamp,
            "author": author[:60],
            "category": category[:30],
            "message": message[:1500],
            "webhook_sent": False
        }

        if webhook_url:
            payload = {
                "username": "Kessler Simulator Feedback",
                "embeds": [{
                    "title": f"[{entry['category']}] Nowa opinia o symulatorze",
                    "description": entry["message"],
                    "color": 3447003,
                    "fields": [
                        {"name": "Autor", "value": entry["author"], "inline": True},
                        {"name": "Źródło", "value": "jifo.dev / Symulator Kesslera", "inline": True}
                    ],
                    "timestamp": timestamp
                }]
            }
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "KesslerSim/1.0"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if 200 <= resp.status < 300:
                    entry["webhook_sent"] = True

        os.makedirs("results", exist_ok=True)
        with open("results/feedback_log.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        status_msg = (
            "Opinia została wysłana na Discorda."
            if entry["webhook_sent"]
            else "Dziękujemy za opinię! Została zapisana lokalnie (webhook Discord nie jest jeszcze podłączony)."
        )
        return jsonify({"ok": True, "message": status_msg, "webhook_sent": entry["webhook_sent"]})

    except Exception as e:
        return jsonify({"error": f"Nie udało się zapisać opinii: {str(e)}"}), 500


@app.route("/api/presets", methods=["GET"])
def get_presets():
    return jsonify(PRESETS)


@app.route("/api/simulate", methods=["POST"])
def simulate():
    try:
        data = request.get_json() or {}
        
        # Pobranie parametrów wejściowych
        g_mult = float(data.get("g_multiplier", 1.0))
        pmd_shift = float(data.get("pmd_shift", 0.0))
        beta_mult = float(data.get("beta_multiplier", 1.0))
        cam_shift = float(data.get("cam_eff_shift", 0.0))
        sat_life = float(data.get("sat_lifetime", 5.0))
        horizon = int(data.get("horizon", 2126))
        mode = data.get("mode", "deterministic")  # "deterministic" lub "monte_carlo"
        mc_samples = int(data.get("mc_samples", 1000))
        target_year = int(data.get("target_year", 2050))
        
        # Utworzenie konfiguracji na podstawie suwaków
        custom_cfgs = create_custom_configs(
            g_multiplier=g_mult,
            pmd_shift=pmd_shift,
            beta_multiplier=beta_mult,
            cam_eff_shift=cam_shift,
            sat_lifetime_override=sat_life
        )
        
        # 1. Symulacja deterministyczna
        df_det = run_deterministic(
            start_year=2026,
            end_year=horizon,
            dt=1.0,
            custom_configs=custom_cfgs
        )
        
        years = df_det["year"].tolist()
        
        # Formatowanie prawdopodobieństw w % (zaokrąglenie do 2 miejsc po przecinku)
        prob_system_pct = [round(float(p) * 100.0, 2) for p in df_det["P_Kessler_any"]]
        prob_med_pct = [round(float(p) * 100.0, 2) for p in df_det["medium_P_Kessler"]]
        prob_high_pct = [round(float(p) * 100.0, 2) for p in df_det["high_P_Kessler"]]
        prob_low_pct = [round(float(p) * 100.0, 2) for p in df_det["low_P_Kessler"]]
        prob_glob_pct = [round(float(p) * 100.0, 2) for p in df_det["global_P_Kessler"]]
        prob_catastrophic_pct = [round(float(p) * 100.0, 2) for p in df_det["P_catastrophic_any"]]
        
        # Współczynniki reprodukcji R_K
        rk_med = [round(float(r), 3) for r in df_det["medium_R_K"]]
        rk_high = [round(float(r), 3) for r in df_det["high_R_K"]]
        rk_low = [round(float(r), 3) for r in df_det["low_R_K"]]
        rk_glob = [round(float(r), 3) for r in df_det["global_R_K"]]
        
        # Populacje satelitów i śmieci (w 100% spójne z modelem globalnym)
        active_med = [int(x) for x in df_det["medium_X"]]
        active_low = [int(x) for x in df_det["low_X"]]
        active_high = [int(x) for x in df_det["high_X"]]
        active_total = [int(x) for x in df_det["global_X"]]
        d10_low = [int(d) for d in df_det["low_D10"]]
        d10_med = [int(d) for d in df_det["medium_D10"]]
        d10_high = [int(d) for d in df_det["high_D10"]]
        d10_total = [int(d) for d in df_det["global_D10"]]
        d1_low = [int(d) for d in df_det["low_D1"]]
        d1_med = [int(d) for d in df_det["medium_D1"]]
        d1_high = [int(d) for d in df_det["high_D1"]]
        d1_total = [int(d) for d in df_det["global_D1"]]
        d01_low = [int(d) for d in df_det["low_D01"]]
        d01_med = [int(d) for d in df_det["medium_D01"]]
        d01_high = [int(d) for d in df_det["high_D01"]]
        d01_total = [int(d) for d in df_det["global_D01"]]

        coll_low = [round(float(c), 4) for c in df_det["low_collisions"]]
        coll_med = [round(float(c), 4) for c in df_det["medium_collisions"]]
        coll_high = [round(float(c), 4) for c in df_det["high_collisions"]]
        coll_total = [round(float(c), 4) for c in df_det["global_collisions"]]
        
        # Kluczowe wskaźniki (KPI) dla roku docelowego
        idx_target = years.index(target_year) if target_year in years else len(years) - 1
        prob_target_pct = prob_system_pct[idx_target]
        prob_med_target_pct = prob_med_pct[idx_target]
        prob_cat_target_pct = prob_catastrophic_pct[idx_target]
        
        # Rok przekroczenia progu R_K = 1 w pasie MEDIUM
        critical_year_med = "Brak (Stabilny)"
        for y, r in zip(years, rk_med):
            if r >= 1.0:
                critical_year_med = str(int(y))
                break
                
        # Szczytowe R_K w pasie MEDIUM i LOW
        peak_rk_med = max(rk_med)
        peak_rk_low = max(rk_low)
        
        # Status i badge
        if peak_rk_med >= 1.0 or peak_rk_low >= 1.0:
            status_text = "Kaskada Kesslera"
            status_badge_class = "px-1.5 py-0.5 rounded text-[10px] font-semibold bg-rose-500/10 text-rose-400"
        elif prob_target_pct >= 20.0 or (len(rk_high) > 5 and max(rk_high[5:]) >= 1.0):
            status_text = "Podwyższone Ryzyko"
            status_badge_class = "px-1.5 py-0.5 rounded text-[10px] font-semibold bg-amber-500/10 text-amber-400"
        else:
            status_text = "Stabilny (R_K < 1)"
            status_badge_class = "px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400"
        
        # Tabela milestones w %
        milestone_years = [2026, 2030, 2035, 2040, 2050, 2060, 2075, 2100]
        milestone_rows = []
        for my in milestone_years:
            if my in years:
                idx_m = years.index(my)
                milestone_rows.append({
                    "year": my,
                    "systemic_pct": f"{prob_system_pct[idx_m]:.1f}%",
                    "medium_pct": f"{prob_med_pct[idx_m]:.1f}%",
                    "high_pct": f"{prob_high_pct[idx_m]:.1f}%",
                    "low_pct": f"{prob_low_pct[idx_m]:.1f}%",
                    "global_pct": f"{prob_glob_pct[idx_m]:.1f}%",
                    "catastrophic_pct": f"{prob_catastrophic_pct[idx_m]:.1f}%",
                    "rk_medium": f"{rk_med[idx_m]:.2f}",
                    "active_satellites": f"{active_total[idx_m]:,}"
                })
                
        response_payload = {
            "mode": mode,
            "years": years,
            "probabilities_percent": {
                "systemic": prob_system_pct,
                "medium": prob_med_pct,
                "high": prob_high_pct,
                "low": prob_low_pct,
                "global": prob_glob_pct,
                "catastrophic_collision": prob_catastrophic_pct
            },
            "reproduction_rk": {
                "medium": rk_med,
                "high": rk_high,
                "low": rk_low,
                "global": rk_glob
            },
            "populations": {
                "active_total": active_total,
                "active_medium": active_med,
                "active_low": active_low,
                "active_high": active_high,
                "d10_low": d10_low,
                "d10_medium": d10_med,
                "d10_high": d10_high,
                "d10_total": d10_total,
                "d1_low": d1_low,
                "d1_medium": d1_med,
                "d1_high": d1_high,
                "d1_total": d1_total,
                "d01_low": d01_low,
                "d01_medium": d01_med,
                "d01_high": d01_high,
                "d01_total": d01_total
            },
            "collisions": {
                "low": coll_low,
                "medium": coll_med,
                "high": coll_high,
                "total": coll_total
            },
            "kpi": {
                "target_year": target_year,
                "prob_target_pct": f"{prob_target_pct:.1f}%",
                "prob_med_target_pct": f"{prob_med_target_pct:.1f}%",
                "prob_cat_target_pct": f"{prob_cat_target_pct:.1f}%",
                "peak_rk_med": f"{peak_rk_med:.2f}",
                "rk_med_2026": f"{rk_med[0]:.2f}",
                "critical_year_med": critical_year_med,
                "status_text": status_text,
                "status_badge_class": status_badge_class,
                "active_sats_2026": f"{active_total[0]:,}".replace(",", " "),
                "active_sats_2035": f"{active_total[years.index(2035)]:,}".replace(",", " ") if 2035 in years else "-"
            },
            "milestones_table": milestone_rows
        }
        
        # 2. Opcjonalne Monte Carlo (gdy użytkownik wybierze tryb MC)
        if mode == "monte_carlo":
            mc_res = run_monte_carlo(
                n_samples=min(2000, max(200, mc_samples)),
                start_year=2026,
                end_year=horizon,
                dt=1.0,
                seed=42,
                custom_configs=custom_cfgs
            )
            # Konwersja percentyli fan chartu na %
            fan_med = mc_res["fan_charts"]["P_Kessler_medium"]
            fan_med_pct = {
                q_key: [round(float(v) * 100.0, 2) for v in q_arr]
                for q_key, q_arr in fan_med.items()
            }
            fan_sys = mc_res["fan_charts"]["P_Kessler_any"]
            fan_sys_pct = {
                q_key: [round(float(v) * 100.0, 2) for v in q_arr]
                for q_key, q_arr in fan_sys.items()
            }
            response_payload["fan_chart_medium_pct"] = fan_med_pct
            response_payload["fan_chart_system_pct"] = fan_sys_pct
            response_payload["empirical_criticality_pct"] = {
                "medium": [round(float(v) * 100.0, 2) for v in mc_res["empirical_criticality"]["medium"]],
                "any": [round(float(v) * 100.0, 2) for v in mc_res["empirical_criticality"]["any"]]
            }
            
            # Wrażliwość (wpływ czynników na prawdopodobieństwo kaskady w pasie MEDIUM LEO)
            sens_df = analyze_sensitivity(mc_res, target_col="P_Kessler_med_2100")
            response_payload["sensitivity"] = sens_df.to_dict(orient="records")
            
        return jsonify(response_payload)
        
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Uruchamianie serwera na http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
