# Ulepszenia Modeli i Zaawansowane Niuanse Fizyczno-Ekonomiczne

W tym dokumencie zebrano analizę dokładności danych wyjściowych oraz propozycje zaawansowanych modyfikacji, które przekształcają uproszczony model w realistyczny symulator ryzyka kaskady Kesslera.

---

## 1. Analiza Dokładności Danych Wstępnych

### Co jest bezwzględnie potwierdzone w najnowszych danych (ESA MASTER-8, stan 2026):
1. **Liczby obiektów:** Wartości ~68.5k (>10 cm), ~1.5 mln (1–10 cm) oraz ~230 mln (1 mm–1 cm) to oficjalny stan z raportu ESA Space Debris Office (luty 2026).
2. **Katalog vs Populacja Modelowana:** Spośród ~68.5k obiektów >10 cm śledzonych regularnie jest ok. 47 140. Różnica wynika z ograniczeń radarów dla obiektów na wysokich orbitach i w martwych strefach.
3. **Skupienie w LEO:** Prawie 30 tys. obiektów katalogowanych i ok. 80% aktywnych satelitów znajduje się w LEO (<2000 km).

### Gdzie pojawiają się istotne niuanse (i jak je kalibrujemy):
1. **Objętość to nie kula (anizotropia):** Zwykła formuła $V_{\text{shell}}$ zawyża rzeczywistą przestrzeń roboczą. Satelity grupują się na konkretnych inklinacjach (Starlink: 53°, OneWeb: 87.9°, satelity teledetekcyjne: 97.5°–98.2° SSO). Wprowadzenie współczynnika $\theta_i \in [0.15, 0.25]$ dla pasm LEO koryguje to skupienie.
2. **Podział na pasma:**
   * **Low (200–600 km):** Zdominowany przez Starlink (~550 km). Czas życia to zaledwie kilka lat.
   * **Medium (600–1100 km):** Najbardziej niebezpieczny pas. Zawiera pozostałości po teście ASAT Fengyun-1C (2007) i zderzeniu Kosmos-Iridium (2009). Czas życia sięga 200 lat.
   * **High (1100–2000 km):** Olbrzymia masa w postaci martwych radzieckich stopni rakietowych SL-8 i SL-16 o masie 1.4–9 ton każdy. Ich rozpad wygenerowałby bezprecedensową chmurę odłamków.

---

## 2. Kluczowe Ulepszenia Fizyczne i Dynamiczne

### Ulepszenie 1: Asymetria Manewrowa (Zdolność CAM a Niewidzialne Odłamki)
Klasyczne modele traktują obiekty homogenicznie. W rzeczywistości ryzyko zderzenia zależy od pary obiektów:
* **$X \times X$ (Aktywny – Aktywny):** Prawie zerowe ryzyko ($P_{\text{CAM}} \approx 99.9\%$), operatorzy współpracują.
* **$X \times D_{10}$ (Aktywny – Duży Odłamek):** Odłamek jest w katalogu. Satelita wykonuje autonomiczny manewr uniku ($P_{\text{CAM}} \approx 95\% - 99\%$).
* **$X \times D_{1}$ (Aktywny – Odłamek 1–10 cm):** **Kluczowy wektor ryzyka!** Odłamki 1–10 cm są niewykrywalne operacyjnie. Satelita nie może wykonać uniku ($P_{\text{CAM}} = 0\%$). Uderzenie niszczy satelitę i zamienia go w pasywny wrak ($X \to D_{10}$) lub rozbija katastroficznie.
* **$D \times D$ (Śmieć – Śmieć):** Brak jakiejkolwiek kontroli ($P_{\text{CAM}} = 0\%$). Wzrost kwadratowy $D^2$.

### Ulepszenie 2: 11-letni Cykl Słoneczny (Modulacja Termosferyczna)
Gęstość atmosfery na wysokości 300–600 km zmienia się nawet 5-krotnie między minimum a maksimum słonecznym. 
W latach maksimum (np. 2024–2026, 2035–2037) pas Low LEO jest gwałtownie czyszczony. W latach minimum śmieci kumulują się szybciej.
Włączamy sinusoidalną modulację oporu $\tau(t) = \tau_0 / [1 + A \cos(2\pi(t - t_{\text{peak}})/11)]$ (w maksimum słonecznym $\cos = +1$, więc $\tau(t)$ spada).

### Ulepszenie 3: Tranzyt i Migracja Między Powłokami ($M_{ij}$)
Odłamki nie znikają natychmiast z orbity:
1. Odłamek z pasa HIGH (np. 1200 km) hamuje niezwykle powoli, wkracza do pasa MEDIUM (1100 km), spędza w nim dekady, a następnie przechodzi przez pas LOW (600 km).
2. Manewry deorbitacyjne satelitów (PMD) wprowadzają trajektorie eliptyczne o perygeum w pasie LOW, co chwilowo zwiększa strumień kolizyjny w niższych warstwach.
3. Rakiety transferowe (GTO) regularnie przecinają wszystkie powłoki LEO.

---

## 3. Ulepszenia Ekonometryczne (Endogeniczny Model Rynkowy)

Tradycyjne modele fizyczne zakładają sztywną ekstrapolację startów ($G(t)$). W ujęciu ekonomicznym podaż startów i zachowanie operatorów reagują na stan środowiska:

### 1. Paradoks Jevonsa w Przemyśle Rakietowym
Gwałtowny spadek kosztu wyniesienia 1 kg ładunku na orbitę (dzięki Starship i rakietom wielorazowym: spadek z \$2000–5000/kg do \$100–300/kg) drastycznie zwiększa popyt na nowe satelity, co przyspiesza zbliżanie się do limitu pojemności orbitalnej.

### 2. Pętla Ubezpieczeniowa i Wartość Zagrożona (Value-at-Risk)
Wzrost gęstości śmieci podnosi składki ubezpieczeniowe satelitów i zmusza do częstszego zużywania paliwa na manewry CAM. W modelu ekonomicznym skutkuje to:
$$G(t) = G_{\text{market}}(t) \cdot \exp\left(-\gamma \cdot \text{RiskFactor}_i(t)\right)$$
Rynek samoczynnie spowalnia starty, gdy ryzyko utraty kapitału przewyższa oczekiwaną stopę zwrotu.

### 3. Regulacyjny Skok Zgodności (Reguła 5 Lat FCC i Karta Zero Debris ESA)
Historyczna reguła dopuszczała pozostawienie satelity na orbicie do 25 lat po zakończeniu misji.
Nowe regulacje FCC skracają ten czas do **5 lat**, a ESA Zero Debris dąży do 99% skutecznego usunięcia.
W modelu parametr $q_i(t)$ (skuteczność deorbitacji) rośnie logistycznie w czasie:
$$q_i(t) = q_{\min} + \frac{q_{\max} - q_{\min}}{1 + e^{-k_q(t - t_{\text{reg}})}}$$

---

## 4. Metodologia Monte Carlo i Rozkłady Niepewności

Aby uzyskać rzetelne przedziały ufności dla prawdopodobieństwa $P(K \le t)$ i wykresy wachlarzowe (*fan charts*), w `src/simulation.py` losujemy mnożniki i przesunięcia parametrów w każdej iteracji:

1. **Mnożnik fragmentacji $\beta_{\text{mult}}$:** $\text{LogNormal}(0, 0.35)$ (ograniczony do $[0.3, 3.5]$)
2. **Mnożnik wzrostu startów i pojemności $g_{\text{mult}}$:** $\text{Normal}(1.0, 0.25)$ (ograniczony do $[0.2, 2.5]$)
3. **Przesunięcie skuteczności deorbitacji $\Delta q_{\text{PMD}}$:** $\text{Normal}(0.0, 0.04)$ (ograniczone do $[-0.15, +0.04]$)
4. **Perturbacja czasu życia odłamków $\tau_{\text{decay}}$:** mnożnik $\text{LogNormal}(0, 0.20)$ (niezależny dla każdej powłoki)
5. **Perturbacja współczynnika koncentracji $\theta_{\text{eff}}$:** mnożnik $\text{LogNormal}(0, 0.25)$ (niezależny dla każdej powłoki)

Dzięki temu obliczamy:
* Krzywe prawdopodobieństwa dla percentyli: $P_{10}(t), P_{25}(t), P_{50}(t), P_{75}(t), P_{90}(t)$.
* Dekompozycję wrażliwości (Global Sensitivity Analysis), pokazującą, które dźwignie polityczno-technologiczne (np. PMD compliance vs redukcja startów) mają największy wpływ na uniknięcie Kesslera.
