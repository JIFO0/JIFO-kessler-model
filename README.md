# Orbital Economics & Kessler Hazard Modeling Framework

Ten projekt implementuje ekonometryczno-fizyczny model ryzyka Syndromu Kesslera ($P(K \le t)$) dla dowolnego horyzontu czasowego (bazowo lata 2026–2126) wraz z interaktywną aplikacją webową (Flask + Chart.js + animowana wizualizacja orbit LEO).

Model łączy mechanikę orbitalną (modele fragmentacji NASA SSBM, gęstości przestrzenne ESA MASTER-8) z teorią ekonomii zasobów wspólnych (Open-Access Commons, model Rao & Rondina 2025) oraz epidemiologicznym wskaźnikiem reprodukcji śmieci kosmicznych ($R_K$).

---

## 1. Główne założenia i struktura 4 modeli

Zamiast naiwnej ekstrapolacji całkowitej liczby obiektów $N(t)$, model analizuje stan i przepływy populacji orbitalnych oraz punkt krytyczny, w którym **produkcja odłamków przewyższa ich naturalne usuwanie** ($R_K \ge 1$).

Analiza prowadzona jest na 4 poziomach:
1. **Model A — GLOBAL (200 – 50 000 km / zagregowany LEO–GEO)**: Spójna agregacja warstw LEO oraz obiektów MEO/GEO (`NON_LEO_BASELINE`).
2. **Model B — LOW (200 – 600 km)**: Pas megakonstelacji (Starlink, Kuiper, Qianfan) z dominującym wpływem oporu atmosferycznego (krótki czas życia $\tau \approx 4\text{ lata}$, silna modulacja 11-letnim cyklem słonecznym).
3. **Model C — MEDIUM (600 – 1100 km)**: Pas o wysokim zagęszczeniu odłamków historycznych (Fengyun-1C, Cosmos-2251, orbity SSO) i długim czasie oczyszczania naturalnego ($\tau \approx 85\text{ lat}$).
4. **Model D — HIGH (1100 – 2000 km)**: Pas o wielowiekowym czasie retencji odłamków ($\tau \approx 1200\text{ lat}$) i obecności ciężkich historycznych stopni rakietowych (SL-8, SL-16).

---

## 2. Struktura repozytorium

```text
├── docs/
│   ├── THEORY_AND_FORMULATIONS.md         # Matematyczny i ekonomiczny opis modeli
│   ├── DATA_CALIBRATION_AND_VALIDATION.md # Weryfikacja danych ESA MASTER-8 / NASA SSBM
│   └── MODEL_IMPROVEMENTS_AND_NUANCES.md  # Niuanse fizyczne (CAM, cykl słoneczny, migracja)
├── src/
│   ├── __init__.py
│   ├── config.py                          # Parametry orbitalne, presety i kalibracja 2026
│   ├── physics.py                         # Objętości efektywne, przekroje, rozpad NASA SSBM
│   ├── models.py                          # Modele powłokowe, migracja i funkcja hazardu
│   ├── simulation.py                      # Silnik deterministyczny i Monte Carlo
│   ├── analysis.py                        # Tabele percentyli, wrażliwość OLS, scenariusze
│   └── visualization.py                   # Generowanie wykresów statycznych (Matplotlib)
├── templates/
│   └── index.html                         # Interaktywny dashboard webowy i animacja orbit LEO
├── results/                               # Wyniki symulacji (CSV, JSON, wykresy PNG)
├── app.py                                 # Serwer Flask i API (/api/simulate, /api/presets)
├── run_baseline.py                        # Skrypt uruchomieniowy (symulacja bazowa)
├── run_monte_carlo.py                     # Skrypt Monte Carlo (domyślnie 2000 prób)
└── README.md
```

---

## 3. Kluczowe zmienne stanu i równania

Dla każdej powłoki $i$:
* $X_i(t)$: Aktywne satelity (posiadające zdolność do manewrów CAM)
* $D_{10, i}(t)$: Niekontrolowane obiekty duże ($>10\text{ cm}$)
* $D_{1, i}(t)$: Odłamki śmiertelne, niekatalogowane ($1\text{ cm} - 10\text{ cm}$)
* $M_{ij}$: Migracja między powłokami w wyniku opadania orbitalnego (`high_to_medium = 0.90`, `medium_to_low = 0.95`)

Wskaźnik reprodukcji Kesslera:
$$R_{K, i}(t) = \frac{\dot{D}_{10, \text{coll}, i}(t)}{\mu_{10, i}(t) \cdot D_{10, i}(t)}$$

Prawdopodobieństwo rozwinięcia kaskady z pojedynczego zderzenia katastroficznego w funkcji $R_K$ (progowy proces gałązkowy):
$$p_{\text{escape}}(R_K) = \begin{cases} 0 & \text{dla } R_K \le 0.80 \\ 0.05 \left(\frac{R_K - 0.80}{0.25}\right)^2 & \text{dla } 0.80 < R_K \le 1.05 \\ 1 - \frac{1}{R_K} & \text{dla } R_K > 1.05 \end{cases}$$

Funkcja hazardu i prawdopodobieństwo wystąpienia kaskady Kesslera do roku $t$:
$$h_i(t) = C_{\text{large}, i}(t) \cdot p_{\text{escape}}(R_{K, i}(t)), \qquad P(K_i \le t) = 1 - \exp\left(-\int_0^t h_i(s)\, ds\right)$$
$$P(K_{\text{any}} \le t) = 1 - \prod_{i \in \{\text{low, med, high}\}} [1 - P(K_i \le t)]$$

---

## 4. Wymagania i uruchomienie

* Python 3.10+
* Pakiety: `flask`, `numpy`, `pandas`, `matplotlib`

Uruchomienie interaktywnego symulatora webowego:
```bash
python app.py
```
Następnie otwórz w przeglądarce `http://localhost:5000`.

Uruchomienie skryptów wsadowych:
```bash
python run_baseline.py
python run_monte_carlo.py --samples 2000
```
