# Kalibracja Danych i Walidacja Źródeł

Niniejszy dokument przedstawia weryfikację i zestawienie danych bazowych wykorzystywanych do kalibracji modeli orbitalnych na rok wyjściowy **2026**, z uwzględnieniem danych Europejskiej Agencji Kosmicznej (ESA), NASA Orbital Debris Program Office (ODPO) oraz literatury naukowej (m.in. Rao & Rondina 2025, Lewis et al., Kessler & Cour-Palais).

---

## 1. Zestawienie Populacji Orbitalnych (Stan na 2026 r.)

### 1.1. Oficjalne Szacunki ESA MASTER-8 (Epoka 1 lutego 2026 r.)

| Kategoria wielkości | Szacowana całkowita liczba obiektów | Odsetek skatalogowany / śledzony | Zagrożenie kinetyczne |
| :--- | :--- | :--- | :--- |
| **> 10 cm** | **68 450** (w tym ~11 300 aktywnych ładunków) | ~69% (katalog śledzi ~47 140 obiektów) | Całkowite zniszczenie, katastroficzna fragmentacja |
| **1 cm – 10 cm** | **1 500 000** (~1.5 mln) | < 1% (niewykrywalne operacyjnie) | Śmiertelne dla każdego satelity; brak możliwości manewru CAM |
| **1 mm – 1 cm** | **230 000 000** (~230 mln) | 0% | Przebicie osłon, degradacja paneli i sensorów |

### 1.2. Rozkład Przestrzenny według Powłok Orbitalnych (Wartości Bazowe dla Modeli)

Na podstawie danych ESA Space Debris Environment Report 2025/2026 oraz bazy DISCOS, populacje w poszczególnych warstwach szacowane są następująco:

| Parametr / Warstwa | Model B: LOW (200–600 km) | Model C: MEDIUM (600–1100 km) | Model D: HIGH (1100–2000 km) | Model A: GLOBAL (200–50 000 km) |
| :--- | :--- | :--- | :--- | :--- |
| **Zakres wysokości ($h$)** | 200 – 600 km | 600 – 1100 km | 1100 – 2000 km | 200 – 50 000 km |
| **Aktywne satelity ($X_0$)** | 7 800 (Starlink, ISS, CSS) | 2 200 (SSO, EO, Iridium) | 1 000 (OneWeb, GNSS prep) | 11 300 (+300 MEO/GEO) |
| **Obiekty >10 cm ($D_{10, 0}$)** | 5 200 | 14 800 (Fengyun-1C, Cosmos-2251) | 8 500 (radzieckie SL-8/16) | 57 150 (+28 650 MEO/GEO) |
| **Odłamki 1–10 cm ($D_{1, 0}$)** | 250 000 | 550 000 | 200 000 | 1 500 000 (+500k MEO/GEO) |
| **Objętość geometryczna ($V_{\text{shell}}$)** | $2.30 \times 10^{11}\text{ km}^3$ | $3.28 \times 10^{11}\text{ km}^3$ | $7.12 \times 10^{11}\text{ km}^3$ | $5.24 \times 10^{14}\text{ km}^3$ |
| **Współczynnik koncentracji ($\theta$)** | 0.15 (skupienie wokół 53° i 550 km) | 0.18 (skupienie polarne SSO 98°) | 0.25 (mniejsze skupienie) | 0.05 (agregat makro) |
| **Średnia prędkość względna ($v_{\text{rel}}$)** | 10.5 km/s | 12.2 km/s | 13.5 km/s | 11.0 km/s |
| **Bazowy czas życia ($\tau_{\text{decay}}$)** | 4.0 lat (silny opór) | 85.0 lat | 1 200.0 lat | 50.0 lat (parametr makro) |
| **Roczna liczba startów ($G_0$)** | 3 200 satelitów/rok | 280 satelitów/rok | 40 satelitów/rok | 3 520 satelitów/rok |
| **Współczynnik sukcesu PMD ($q_0$)** | 96% | 90% | 85% | 95% |

---

## 2. Walidacja Wzorców Fragmentacji (NASA SSBM)

Zgodnie z NASA Standard Satellite Breakup Model (Johnson et al. 2001):
* **Próg katastroficzny:** Energia kinetyczna uderzenia $E_k / M_{\text{target}} \ge 40\text{ kJ/kg}$. Przy względnej prędkości $10\text{ km/s}$, uderzenie obiektu o masie zaledwie $100\text{ g}$ (rozmiar $\sim 4-5\text{ cm}$) niesie energię $5\text{ MJ}$, co wystarcza do rozbicia 125 kg satelity. Obiekt o wielkości 10 cm niszczy satelitę o masie do kilku ton!
* **Dystrybucja fragmentów:**
  $$N(L_c) = 0.1 \cdot M^{0.75} \cdot L_c^{-1.71}$$
  Dla średniej masy zderzeniowej $M = 1200\text{ kg}$:
  - $L_c \ge 0.1\text{ m}$ ($>10\text{ cm}$): $\beta_{10} \approx 0.1 \cdot (1200)^{0.75} \cdot (0.1)^{-1.71} \approx 1030$ odłamków.
  - $L_c \ge 0.01\text{ m}$ ($>1\text{ cm}$): $\beta_{1} \approx 0.1 \cdot (1200)^{0.75} \cdot (0.01)^{-1.71} \approx 52\,800$ odłamków.
* **Kalibracja Rao & Rondina (2025):** W modelu Rao i Rondiny przyjęto bazową wartość $\beta_{DD} \approx 332$ dla odłamków zdatnych do wywołania kolejnej fragmentacji w węższym zakresie masowym. W naszym ujęciu przyjmujemy rozkład log-normalny:
  $$\beta \sim \text{LogNormal}(\mu = \ln(800), \sigma = 0.45)$$
  dla obiektów $>10\text{ cm}$, oraz proporcjonalnie wyższy dla $1-10\text{ cm}$.

---

## 3. Dynamika Atmosferyczna i Cykl Słoneczny

Gęstość termosfery $\rho(h)$ podlega 11-letniemu cyklowi aktywności słonecznej (strumień promieniowania $F_{10.7}$). W okresie maksimum aktywności słonecznej (np. 2024–2026) atmosfera rozszerza się, skracając czas życia obiektów na wysokości 300–550 km nawet 3- do 5-krotnie w porównaniu z minimum słonecznym (np. 2030–2032).

Model oporu atmosferycznego (w maksimum słonecznym opór rośnie, więc $\tau_{\text{decay}}$ maleje):
$$\tau_{\text{decay}, i}(t) = \frac{\tau_{0, i}}{1 + A_{\text{solar}, i} \cdot \cos\left(\frac{2\pi (t - t_{\text{solar\_max}})}{11}\right)}$$
gdzie dla powłoki LOW $A_{\text{solar}} = 0.55$, dla MEDIUM $A_{\text{solar}} = 0.20$, natomiast dla powłoki HIGH wpływ ten niemal zanika ($A_{\text{solar}} = 0.02$).
