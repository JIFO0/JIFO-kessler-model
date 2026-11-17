# Teoria, Formuły Matematyczne i Architektura Modeli Kesslera

Niniejszy dokument formalizuje matematyczny, fizyczny i ekonometryczny model dynamiki populacji orbitalnych oraz prawdopodobieństwa wejścia w kaskadę Kesslera ($P(K \le t)$).

---

## 1. Perspektywa Ekonomiczna: Orbita jako Zasób Wspólny (Common-Pool Resource)

Zgodnie z ujęciem ekonomicznym (Rao & Rondina 2025, Adilov et al. 2020), orbita okołoziemska posiada cechy **otwartego zasobu wspólnego (Open-Access Commons)**:
* **Brak wykluczalności (Non-excludability):** Każdy podmiot posiadający technologię rakietową może umieścić ładunek na orbicie.
* **Rywalizacyjność (Rivalry):** Każdy wprowadzony obiekt zajmuje przestrzeń fazową i generuje ryzyko kolizyjne dla wszystkich pozostałych użytkowników (negatywny efekt zewnętrzny - *negative externality*).

W odróżnieniu od klasycznych zasobów odnawialnych (np. rybołówstwo Gordon-Schaefer), przestrzeń orbitalna wykazuje **dodatnie sprzężenie zwrotne w degradacji (autokatalityczny rozpad)**:
Zniszczenie kapitału orbitalnego (satelity) nie redukuje presji na zasób, lecz zwielokrotnia liczbę obiektów zagrażających ($1 \text{ satelita} \to \beta \text{ niekontrolowanych pocisków}$).

---

## 2. Podział Przestrzeni Orbitalnej (4 Modele)

Definiujemy promień Ziemi jako $R_E \approx 6378.137\text{ km}$. Promień orbitalny $r = R_E + h$.

Pojemność geometryczna powłoki sferycznej o wysokości od $h_1$ do $h_2$:
$$V_{\text{shell}} = \frac{4}{3}\pi \left[(R_E + h_2)^3 - (R_E + h_1)^3\right]$$

Jednak obiekty kosmiczne nie wypełniają kuli izotropowo – orbitują w dyskach nachylonych do równika pod kątami inklinacji $i$, z wyraźnymi klastrami (53° dla Starlink, 97-98° dla orbit heliosynchronicznych SSO).
Wprowadzamy **efektywną objętość orbitalną**:
$$V_{\text{eff}, i} = V_{\text{shell}, i} \cdot \theta_i$$
gdzie $\theta_i \in (0, 1]$ jest **współczynnikiem koncentracji przestrzennej** wyznaczanym z gęstości ESA MASTER-8.

### Podział na modele:
1. **Model A (GLOBAL):** $h \in [200, 50\,000]\text{ km}$ (LEO, MEO, GEO – model makro).
2. **Model B (LOW LEO):** $h \in [200, 600]\text{ km}$. Silna atmosfera, czasy życia od miesięcy do paru lat.
3. **Model C (MEDIUM LEO):** $h \in [600, 1100]\text{ km}$. Kluczowy pas: megakonstelacje, SSO, historyczne satelity naukowe. Słabe hamowanie atmosferyczne.
4. **Model D (HIGH LEO):** $h \in [1100, 2000]\text{ km}$. Górny LEO. Czas retencji od stuleci do tysiącleci. Duże opuszczone radzieckie i amerykańskie stopnie rakietowe (SL-8, SL-16).

---

## 3. Zmienne Stanu Populacji Orbitalnej

Dla każdego reżimu $i \in \{B, C, D\}$ (oraz w modelu globalnym $A$):
* $X_i(t)$: Liczba **aktywnych satelitów** zdolnych do unikania zderzeń (CAM - *Collision Avoidance Maneuvers*).
* $D_{10, i}(t)$: Liczba niekontrolowanych dużych obiektów ($> 10\text{ cm}$) – katalogowanych i śledzonych z Ziemi.
* $D_{1, i}(t)$: Liczba odłamków śmiertelnych niekatalogowanych ($1\text{ cm} - 10\text{ cm}$) – niewidocznych dla radarów operacyjnych, niszczących satelitę w razie uderzenia.
* $D_{01, i}(t)$: Mikroodłamki erozyjne ($1\text{ mm} - 1\text{ cm}$) – ok. 230 mln obiektów (ESA MASTER-8), powodujące erozję i awarie podsystemów ($p_{\text{kill}} = 0.015$).

Całkowita populacja obiektów krytycznych:
$$N_i(t) = X_i(t) + D_{10, i}(t) + D_{1, i}(t)$$

---

## 4. Kinetyka Zderzeń i Unikanie Kolizji

Liczba zderzeń w jednostce czasu (rok) wynika z kinetycznej teorii gazów z uwzględnieniem aktywnych manewrów satelitów:

$$C_i(t) = C_{X \times X, i}(t) + C_{X \times D, i}(t) + C_{D \times D, i}(t)$$

Dla dwóch populacji o liczności $N_A, N_B$, średniej prędkości względnej $v_{\text{rel}, i} \approx 10 - 14\text{ km/s}$ i przekroju czynnym zderzenia $\sigma_{AB} = \pi (r_A + r_B)^2$:

$$C_{AB, i} = \frac{N_A \cdot N_B \cdot \sigma_{AB} \cdot v_{\text{rel}, i}}{V_{\text{eff}, i}} \cdot (1 - P_{\text{CAM}, AB})$$

Gdzie współczynnik unikania zderzenia $P_{\text{CAM}}$ wynosi:
* Dla $X \times X$: $P_{\text{CAM}} \approx 0.999$ (obie strony manewrują).
* Dla $X \times D_{10}$: $P_{\text{CAM}} \approx 0.95 - 0.99$ (odłamek jest śledzony, satelita wykonuje manewr).
* Dla $X \times D_{1}$: $P_{\text{CAM}} \approx 0.0$ (odłamek $1-10\text{ cm}$ NIE jest śledzony w katalogu – satelita jest ślepy!).
* Dla $D \times D$: $P_{\text{CAM}} = 0.0$ (żaden obiekt nie steruje).

To rozróżnienie jest fundamentalne: **wzrost populacji odłamków $1-10\text{ cm}$ neutralizuje korzyści z aktywnych systemów CAM**.

---

## 5. Fizyka Fragmentacji (NASA Standard Satellite Breakup Model)

W kolizji katastroficznej (energia uderzenia $> 40\text{ J/g}$ masy celu), liczba generowanych odłamków o charakterystycznym wymiarze $L_c \ge d$ opisana jest prawem potęgowym NASA SSBM:

$$N(L_c) = 0.1 \cdot (M_{\text{impact}})^{0.75} \cdot L_c^{-1.71}$$

gdzie $M_{\text{impact}}$ jest sumaryczną masą zderzających się obiektów (w kg), a $L_c$ jest w metrach.

Dla typowej kolizji satelita-satelita ($M \approx 1000 - 2000\text{ kg}$):
* Odłamki $> 10\text{ cm}$ ($L_c \ge 0.1\text{ m}$): $\beta_{10} \sim 800 - 1500$
* Odłamki $> 1\text{ cm}$ ($L_c \ge 0.01\text{ m}$): $\beta_{1} \sim 40\,000 - 75\,000$

W modelu wprowadzamy stochastyczny rozkład $\beta \sim \text{LogNormal}(\mu_\beta, \sigma_\beta)$ uwzględniający różnorodność mas obiektów (od cubesatów 5 kg po stopnie rakiet Zenit 9000 kg).

---

## 6. Układ Równań Różniczkowych Stanu i Migracja Między Powłokami

Równania bilansu dla strefy $i$:

$$\frac{d X_i}{dt} = G_i(t) - \frac{1}{\tau_{\text{life}, i}} X_i(t) - C_{X, i}(t)$$

$$\frac{d D_{10, i}}{dt} = \frac{(1 - q_i)}{\tau_{\text{life}, i}} X_i(t) + \sum_{k} \beta_{10, k} C_{k, i}(t) - \mu_i(t) D_{10, i}(t) + M_{10, \text{in}, i}(t) - M_{10, \text{out}, i}(t)$$

$$\frac{d D_{1, i}}{dt} = \sum_{k} \beta_{1, k} C_{k, i}(t) - \mu_{1, i}(t) D_{1, i}(t) + M_{1, \text{in}, i}(t) - M_{1, \text{out}, i}(t)$$

Gdzie:
* $G_i(t)$: Napływ nowych ładunków (launch rate) według funkcji logistycznej:
  $$G_i(t) = \frac{K_i}{1 + \left(\frac{K_i - G_{0, i}}{G_{0, i}}\right) e^{-g_i t}}$$
* $q_i(t)$: Skuteczność usuwania satelitów po zakończeniu misji (Post-Mission Disposal - PMD compliance rate, np. 90-99%).
* $\tau_{\text{life}, i}$: Średni czas operacyjny satelity (typowo 5-7 lat).
* $\mu_i(t) = 1 / \tau_{\text{decay}, i}(t)$: Tempo naturalnego opadania w atmosferze.
* $M_{ij}$: Macierz migracji – odłamki opadające z wyższej powłoki $j$ spędzają pewien czas tranzytu w powłoce niższej $i$ przed spaleniem.

---

## 7. Liczba Reprodukcyjna Kesslera ($R_K$)

W analogii do współczynnika $R_0$ w epidemiologii:

$$R_{K, i}(t) = \frac{\text{tempo generowania nowych trwałych odłamków przez kolizje}}{\text{tempo naturalnego usuwania odłamków przez reentry}}$$

$$R_{K, i}(t) = \beta_i \cdot P_{\text{coll\_per\_object}, i}(t) \cdot \tau_{\text{decay}, i}(t)$$

Interpretacja reżimów:
* $R_{K, i} < 1$: **Układ stabilny**. Usunięcie przez atmosferę przewyższa kreację zderzeniową.
* $R_{K, i} = 1$: **Punkt krytyczny (Criticality Threshold)**.
* $R_{K, i} > 1$: **Samonapędzająca się kaskada (Kessler Runaway)**. Populacja śmieci rośnie wykładniczo nawet przy całkowitym wstrzymaniu nowych startów rakietowych ($G_i = 0$).

---

## 8. Funkcja Hazardu i Prawdopodobieństwo Kaskady Kesslera $P(K \le t)$

Chwilowe natężenie ryzyka zainicjowania samonapędzającej się kaskady Kesslera wyznaczane jest w oparciu o teorię procesów gałązkowych (Branching Processes) oraz kinetykę zderzeń katastroficznych NASA ODPO.

W modelu zaimplementowano dwa reżimy hazardu (konfigurowalne w `HAZARD_CONFIG`):

1. **Progowy gładki model gałązkowy (Smooth Branching Hazard — domyślny):**
   W reżimie podkrytycznym ($R_K \le 0.80$) pojedyncze kolizje generują skończoną chmurę odłamków, która ulega naturalnemu rozpadowi w atmosferze ($p_{\text{escape}} = 0$). W pasie przejściowym ($0.80 < R_K \le 1.05$) uwzględniana jest lokalna anizotropia przestrzenna, a powyżej progu $R_K > 1.05$ funkcja przechodzi w klasyczne prawdopodobieństwo ucieczki procesu gałązkowego $1 - 1/R_K$:
   $$p_{\text{escape}}(R_K) = \begin{cases} 0 & \text{dla } R_K \le 0.80 \\ 0.05 \left(\frac{R_K - 0.80}{0.25}\right)^2 & \text{dla } 0.80 < R_K \le 1.05 \\ 1 - \frac{1}{R_K} & \text{dla } R_K > 1.05 \end{cases}$$
   $$h_i(t) = C_{\text{catastrophic}, i}(t) \cdot p_{\text{escape}}(R_{K, i}(t))$$

2. **Ścisły skokowy proces gałązkowy (Pure Branching Hazard):**
   $$h_i(t) = \begin{cases} 0 & \text{dla } R_{K, i}(t) \le 1.0 \\ C_{\text{catastrophic}, i}(t) \cdot \left(1 - \frac{1}{R_{K, i}(t)}\right) & \text{dla } R_{K, i}(t) > 1.0 \end{cases}$$

Prawdopodobieństwo, że powłoka $i$ wejdzie w kaskadę Kesslera do roku $t$:
$$P(K_i \le t) = 1 - \exp\left(-\int_0^t h_i(s)\, ds\right)$$

Prawdopodobieństwo zdarzenia w **przynajmniej jednej powłoce orbitalnej**:
$$P(K_{\text{any}} \le t) = 1 - \prod_{i \in \{B, C, D\}} \left[1 - P(K_i \le t)\right]$$

Równolegle model kalkuluje prawdopodobieństwo Poissona wystąpienia przynajmniej jednej katastroficznej kolizji fragmentacyjnej w LEO:
$$P_{\text{catastrophic\_coll}}(\le t) = 1 - \exp\left(-\int_0^t C_{\text{large, any}}(s)\, ds\right)$$
