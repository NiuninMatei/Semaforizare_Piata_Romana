# Rezultate – evaluare comparativă

Medii ± abatere standard pe 5 seed-uri SUMO. Procentele sunt față de plan fix de referință. Mediana pe seed-uri este dată separat pentru așteptarea vehiculelor: aproape de saturație, rețeaua poate intra sau nu în blocaj în funcție de seed, iar câteva rulări blocate trag media în sus. Generat automat de `python -m romana.control.evaluate`.


## Scenariul `zi_2026-10-21_linistit`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 46.1 ± 1.5 | 45.2 | 85.2 ± 1.6 | 5.2 ± 0.9 | 208.7 ± 1.7 | 4.3 ± 0.3 | 1074 ± 0 | 72 ± 5 | 689 ± 4 |
| Plan fix (Webster) | 101.9 ± 42.1 (+121%) | 82.3 (+82%) | 150.1 ± 48.0 | 4.5 ± 0.8 | 273.6 ± 47.8 | 10.1 ± 3.1 | 1074 ± 0 | 68 ± 3 | 808 ± 85 |
| Actuated SUMO | 45.1 ± 5.4 (-2%) | 42.9 (-5%) | 83.1 ± 6.4 | 6.8 ± 2.0 | 206.7 ± 6.5 | 3.9 ± 0.6 | 1074 ± 0 | 65 ± 5 | 683 ± 12 |
| Max-Pressure | 61.9 ± 16.0 (+34%) | 57.4 (+27%) | 105.4 ± 19.9 | 3.6 ± 0.3 | 228.9 ± 19.7 | 6.1 ± 1.2 | 1074 ± 0 | 63 ± 4 | 735 ± 34 |
| Agent RL (PPO) | 52.8 ± 7.9 (+15%) | 48.9 (+8%) | 93.8 ± 9.1 | 4.8 ± 1.5 | 217.3 ± 9.0 | 4.6 ± 0.8 | 1074 ± 0 | 80 ± 25 | 714 ± 17 |
| Agent RL v2 (cozi în amonte) | 47.6 ± 10.0 (+3%) | 41.0 (-9%) | 87.1 ± 12.0 | 4.4 ± 0.9 | 210.6 ± 12.1 | 4.1 ± 1.5 | 1074 ± 0 | 75 ± 16 | 696 ± 23 |
| Agent RL v3 (imitație + PPO) | 49.5 ± 1.0 (+7%) | 49.4 (+9%) | 88.1 ± 1.5 | 5.9 ± 1.2 | 211.6 ± 1.7 | 5.2 ± 0.2 | 1074 ± 0 | 78 ± 5 | 694 ± 5 |
| Agent RL coridor (piață + 4 vecini) | 52.0 ± 1.5 (+13%) | 52.5 (+16%) | 91.4 ± 1.7 | 4.9 ± 0.8 | 214.9 ± 1.9 | 3.9 ± 0.2 | 1074 ± 0 | 68 ± 4 | 707 ± 4 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 34.0 ± 5.9 | 65.8 ± 4.5 | 154.0 ± 1.2 | 12.3 ± 0.2 | 112.1 ± 0.5 |
| Plan fix (Webster) | 193.7 ± 122.8 | 252.1 ± 142.6 | 134.1 ± 4.7 (-13%) | 7.0 ± 0.5 | 120.5 ± 17.2 (+7%) |
| Actuated SUMO | 47.4 ± 24.2 | 79.9 ± 25.7 | 146.7 ± 4.3 (-5%) | 10.2 ± 0.7 | 107.9 ± 4.4 (-4%) |
| Max-Pressure | 58.4 ± 25.1 | 95.8 ± 25.1 | 124.0 ± 1.4 (-19%) | 5.5 ± 0.3 | 101.1 ± 6.8 (-10%) |
| Agent RL (PPO) | 49.7 ± 13.3 | 88.2 ± 18.8 | 139.8 ± 19.2 (-9%) | 7.6 ± 2.4 | 106.7 ± 9.5 (-5%) |
| Agent RL v2 (cozi în amonte) | 50.1 ± 35.5 | 86.4 ± 42.5 | 136.4 ± 15.8 (-11%) | 7.6 ± 1.6 | 102.7 ± 11.8 (-8%) |
| Agent RL v3 (imitație + PPO) | 42.0 ± 9.8 | 75.1 ± 13.5 | 168.3 ± 1.2 (+9%) | 17.3 ± 0.3 | 121.1 ± 0.9 (+8%) |
| Agent RL coridor (piață + 4 vecini) | 48.1 ± 11.3 | 84.0 ± 10.6 | 132.0 ± 3.0 (-14%) | 7.4 ± 0.7 | 101.7 ± 2.2 (-9%) |

## Scenariul `zi_2026-10-21_linistit_x0_8`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 44.4 ± 0.7 | 44.2 | 82.1 ± 0.8 | 4.1 ± 0.3 | 206.9 ± 0.8 | 3.1 ± 0.2 | 859 ± 0 | 70 ± 3 | 549 ± 2 |
| Plan fix (Webster) | 51.7 ± 8.8 (+16%) | 48.7 (+10%) | 91.5 ± 10.0 | 5.0 ± 0.6 | 216.2 ± 10.0 | 4.2 ± 0.9 | 859 ± 0 | 76 ± 23 | 569 ± 15 |
| Actuated SUMO | 45.6 ± 6.8 (+3%) | 41.3 (-7%) | 83.2 ± 7.1 | 5.7 ± 1.8 | 207.9 ± 7.2 | 2.9 ± 0.5 | 859 ± 0 | 61 ± 2 | 550 ± 9 |
| Max-Pressure | 54.6 ± 7.7 (+23%) | 51.8 (+17%) | 95.3 ± 8.3 | 3.6 ± 0.7 | 220.0 ± 8.4 | 4.2 ± 0.8 | 859 ± 0 | 57 ± 4 | 578 ± 12 |
| Agent RL (PPO) | 49.4 ± 5.5 (+11%) | 50.3 (+14%) | 88.4 ± 5.5 | 3.7 ± 0.4 | 213.1 ± 5.5 | 3.1 ± 0.5 | 859 ± 0 | 62 ± 5 | 565 ± 6 |
| Agent RL v2 (cozi în amonte) | 41.3 ± 0.9 (-7%) | 41.4 (-6%) | 79.5 ± 1.2 | 4.3 ± 0.8 | 204.2 ± 1.0 | 2.4 ± 0.1 | 859 ± 0 | 64 ± 3 | 551 ± 3 |
| Agent RL v3 (imitație + PPO) | 52.5 ± 3.1 (+18%) | 52.9 (+20%) | 90.7 ± 3.1 | 6.1 ± 0.9 | 215.5 ± 3.1 | 4.4 ± 0.4 | 859 ± 0 | 76 ± 2 | 560 ± 4 |
| Agent RL coridor (piață + 4 vecini) | 56.4 ± 17.0 (+27%) | 49.2 (+11%) | 94.9 ± 18.0 | 4.7 ± 1.0 | 219.6 ± 17.8 | 3.4 ± 1.6 | 859 ± 0 | 64 ± 3 | 571 ± 25 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 13.6 ± 13.6 | 28.2 ± 15.7 | 153.1 ± 1.2 | 11.6 ± 0.2 | 105.1 ± 0.6 |
| Plan fix (Webster) | 40.0 ± 5.6 | 59.4 ± 5.4 | 139.8 ± 16.9 (-9%) | 10.3 ± 6.8 | 100.2 ± 9.1 (-5%) |
| Actuated SUMO | 27.2 ± 20.0 | 45.3 ± 23.9 | 142.2 ± 4.3 (-7%) | 8.9 ± 0.8 | 99.8 ± 3.7 (-5%) |
| Max-Pressure | 36.8 ± 5.6 | 58.6 ± 5.2 | 121.3 ± 1.4 (-21%) | 4.6 ± 0.4 | 90.6 ± 2.6 (-14%) |
| Agent RL (PPO) | 21.2 ± 15.1 | 39.1 ± 15.2 | 124.7 ± 0.6 (-19%) | 5.5 ± 0.3 | 90.9 ± 1.5 (-14%) |
| Agent RL v2 (cozi în amonte) | 32.4 ± 16.8 | 51.4 ± 17.9 | 128.6 ± 1.0 (-16%) | 6.3 ± 0.2 | 91.0 ± 0.5 (-13%) |
| Agent RL v3 (imitație + PPO) | 17.2 ± 13.6 | 33.8 ± 17.7 | 168.2 ± 1.5 (+10%) | 16.7 ± 0.4 | 116.0 ± 1.5 (+10%) |
| Agent RL coridor (piață + 4 vecini) | 63.0 ± 55.5 | 85.7 ± 57.4 | 134.5 ± 5.9 (-12%) | 7.5 ± 0.9 | 98.1 ± 7.5 (-7%) |

## Scenariul `zi_2026-10-21_pranz`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 111.0 ± 8.2 | 106.5 | 165.7 ± 9.1 | 108.4 ± 6.2 | 283.8 ± 9.3 | 18.4 ± 1.1 | 1908 ± 20 | 144 ± 23 | 1402 ± 21 |
| Plan fix (Webster) | 106.0 ± 9.4 (-5%) | 104.0 (-2%) | 160.3 ± 10.4 | 109.1 ± 14.0 | 278.3 ± 10.5 | 17.3 ± 1.3 | 1894 ± 30 | 189 ± 91 | 1379 ± 25 |
| Actuated SUMO | 118.5 ± 19.5 (+7%) | 121.8 (+14%) | 175.0 ± 21.7 | 38.1 ± 12.8 | 293.5 ± 21.7 | 22.0 ± 3.2 | 1949 ± 0 | 165 ± 68 | 1455 ± 71 |
| Max-Pressure | 121.4 ± 16.4 (+9%) | 127.8 (+20%) | 182.2 ± 19.4 | 136.9 ± 9.8 | 300.2 ± 19.3 | 20.6 ± 2.2 | 1879 ± 24 | 166 ± 19 | 1456 ± 50 |
| Agent RL (PPO) | 91.5 ± 7.5 (-18%) | 87.8 (-17%) | 146.2 ± 8.0 | 120.3 ± 21.2 | 264.4 ± 7.9 | 14.3 ± 1.3 | 1923 ± 25 | 126 ± 26 | 1356 ± 16 |
| Agent RL v2 (cozi în amonte) | 96.0 ± 42.9 (-14%) | 76.1 (-29%) | 150.6 ± 48.3 | 65.2 ± 47.5 | 269.0 ± 48.4 | 16.7 ± 7.1 | 1942 ± 8 | 179 ± 85 | 1380 ± 159 |
| Agent RL v3 (imitație + PPO) | 122.6 ± 21.4 (+10%) | 117.7 (+11%) | 179.9 ± 24.2 | 96.0 ± 21.1 | 298.1 ± 24.0 | 21.6 ± 2.9 | 1921 ± 35 | 189 ± 93 | 1454 ± 66 |
| Agent RL coridor (piață + 4 vecini) | 364.2 ± 36.9 (+228%) | 355.3 (+234%) | 457.3 ± 41.9 | 117.4 ± 17.3 | 570.1 ± 41.8 | 20.0 ± 3.5 | 1696 ± 61 | 371 ± 47 | 2200 ± 91 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 149.4 ± 9.3 | 198.7 ± 10.8 | 153.6 ± 2.0 | 13.3 ± 0.5 | 244.0 ± 8.5 |
| Plan fix (Webster) | 154.9 ± 7.3 | 209.2 ± 7.6 | 148.7 ± 29.0 (-3%) | 8.9 ± 0.3 | 237.8 ± 29.3 (-3%) |
| Actuated SUMO | 94.3 ± 20.1 | 134.6 ± 23.6 | 222.7 ± 32.8 (+45%) | 26.0 ± 4.4 | 255.3 ± 14.2 (+5%) |
| Max-Pressure | 204.8 ± 75.3 | 264.5 ± 80.5 | 136.3 ± 4.6 (-11%) | 9.2 ± 0.8 | 256.0 ± 15.5 (+5%) |
| Agent RL (PPO) | 130.8 ± 15.6 | 182.9 ± 17.5 | 140.7 ± 3.4 (-8%) | 10.7 ± 1.0 | 232.3 ± 15.2 (-5%) |
| Agent RL v2 (cozi în amonte) | 124.7 ± 87.2 | 166.7 ± 92.2 | 191.4 ± 33.9 (+25%) | 15.0 ± 3.6 | 237.2 ± 51.4 (-3%) |
| Agent RL v3 (imitație + PPO) | 133.2 ± 30.4 | 183.8 ± 33.5 | 196.1 ± 42.4 (+28%) | 23.1 ± 6.0 | 272.1 ± 47.0 (+11%) |
| Agent RL coridor (piață + 4 vecini) | 526.7 ± 124.0 | 611.8 ± 131.3 | 145.8 ± 8.1 (-5%) | 10.5 ± 1.4 | 389.6 ± 26.9 (+60%) |

## Scenariul `zi_2026-10-21_varf`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 135.4 ± 16.1 | 126.0 | 198.9 ± 17.6 | 104.9 ± 4.5 | 323.8 ± 18.0 | 28.8 ± 2.5 | 2404 ± 15 | 498 ± 171 | 1838 ± 62 |
| Plan fix (Webster) | 203.8 ± 70.7 (+51%) | 186.0 (+48%) | 273.9 ± 74.5 | 111.7 ± 10.4 | 395.5 ± 72.0 | 38.8 ± 7.7 | 2355 ± 114 | 520 ± 183 | 2141 ± 259 |
| Actuated SUMO | 231.8 ± 35.1 (+71%) | 221.8 (+76%) | 306.2 ± 39.7 | 78.8 ± 10.5 | 428.5 ± 39.2 | 44.2 ± 3.7 | 2442 ± 39 | 447 ± 106 | 2326 ± 146 |
| Max-Pressure | 172.2 ± 17.8 (+27%) | 176.7 (+40%) | 246.3 ± 21.9 | 86.1 ± 15.6 | 370.9 ± 22.1 | 34.6 ± 2.9 | 2282 ± 37 | 653 ± 178 | 1958 ± 82 |
| Agent RL (PPO) | 143.5 ± 35.3 (+6%) | 124.1 (-2%) | 211.0 ± 38.6 | 96.6 ± 29.3 | 336.3 ± 39.2 | 28.6 ± 5.6 | 2333 ± 44 | 523 ± 58 | 1840 ± 123 |
| Agent RL v2 (cozi în amonte) | 127.0 ± 45.3 (-6%) | 107.6 (-15%) | 192.1 ± 50.0 | 115.6 ± 15.7 | 316.5 ± 49.7 | 26.5 ± 8.1 | 2392 ± 38 | 453 ± 134 | 1813 ± 174 |
| Agent RL v3 (imitație + PPO) | 138.9 ± 31.6 (+3%) | 124.6 (-1%) | 203.1 ± 36.1 | 98.2 ± 11.2 | 327.5 ± 36.7 | 30.6 ± 5.0 | 2443 ± 37 | 408 ± 73 | 1879 ± 121 |
| Agent RL coridor (piață + 4 vecini) | 392.8 ± 54.0 (+190%) | 413.4 (+228%) | 510.1 ± 67.6 | 135.9 ± 45.3 | 630.0 ± 68.9 | 31.5 ± 9.5 | 2144 ± 48 | 656 ± 57 | 2879 ± 260 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 230.9 ± 34.1 | 299.4 ± 36.2 | 187.6 ± 35.9 | 20.2 ± 3.9 | 335.7 ± 27.4 |
| Plan fix (Webster) | 226.1 ± 54.9 | 297.3 ± 60.6 | 178.5 ± 16.0 (-5%) | 15.8 ± 3.3 | 389.7 ± 58.3 (+16%) |
| Actuated SUMO | 257.1 ± 78.7 | 322.6 ± 84.7 | 227.3 ± 15.4 (+21%) | 32.1 ± 3.7 | 428.0 ± 34.1 (+28%) |
| Max-Pressure | 397.6 ± 60.5 | 477.4 ± 63.0 | 183.1 ± 34.0 (-2%) | 14.1 ± 1.2 | 346.3 ± 38.8 (+3%) |
| Agent RL (PPO) | 326.8 ± 78.3 | 399.2 ± 78.1 | 178.0 ± 21.0 (-5%) | 16.6 ± 3.1 | 327.9 ± 27.8 (-2%) |
| Agent RL v2 (cozi în amonte) | 296.6 ± 89.6 | 368.5 ± 93.8 | 171.0 ± 25.0 (-9%) | 17.3 ± 3.9 | 328.5 ± 42.4 (-2%) |
| Agent RL v3 (imitație + PPO) | 216.8 ± 49.8 | 283.2 ± 55.2 | 184.7 ± 15.2 (-2%) | 20.2 ± 1.2 | 335.2 ± 25.7 (-0%) |
| Agent RL coridor (piață + 4 vecini) | 547.6 ± 102.6 | 651.6 ± 112.4 | 158.3 ± 10.5 (-16%) | 13.7 ± 2.7 | 535.5 ± 41.4 (+60%) |

## Scenariul `zi_2026-10-21_varf_x1_2`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 206.6 ± 39.9 | 195.0 | 284.1 ± 46.6 | 94.4 ± 11.6 | 409.2 ± 46.4 | 43.6 ± 4.7 | 2791 ± 29 | 572 ± 55 | 2537 ± 211 |
| Plan fix (Webster) | 212.2 ± 16.3 (+3%) | 216.5 (+11%) | 288.9 ± 18.6 | 87.0 ± 10.9 | 411.8 ± 18.7 | 46.5 ± 2.6 | 2792 ± 33 | 572 ± 54 | 2599 ± 88 |
| Actuated SUMO | 307.5 ± 53.4 (+49%) | 289.5 (+48%) | 404.0 ± 59.6 | 66.2 ± 11.8 | 525.9 ± 59.0 | 51.0 ± 3.7 | 2808 ± 71 | 631 ± 52 | 3168 ± 240 |
| Max-Pressure | 276.1 ± 69.8 (+34%) | 267.7 (+37%) | 364.6 ± 75.5 | 55.9 ± 16.2 | 487.5 ± 73.7 | 49.6 ± 6.8 | 2551 ± 145 | 894 ± 193 | 2752 ± 255 |
| Agent RL (PPO) | 232.4 ± 64.1 (+13%) | 237.8 (+22%) | 319.0 ± 74.3 | 71.4 ± 21.5 | 444.2 ± 72.6 | 41.6 ± 5.2 | 2648 ± 128 | 809 ± 281 | 2578 ± 282 |
| Agent RL v2 (cozi în amonte) | 235.3 ± 67.9 (+14%) | 230.9 (+18%) | 316.7 ± 77.3 | 97.5 ± 14.0 | 440.3 ± 76.0 | 44.9 ± 8.7 | 2695 ± 80 | 948 ± 239 | 2637 ± 318 |
| Agent RL v3 (imitație + PPO) | 244.4 ± 95.5 (+18%) | 213.7 (+10%) | 324.3 ± 105.5 | 79.8 ± 16.4 | 447.7 ± 103.2 | 47.7 ± 10.7 | 2742 ± 137 | 648 ± 174 | 2698 ± 424 |
| Agent RL coridor (piață + 4 vecini) | 513.5 ± 121.3 (+149%) | 479.9 (+146%) | 652.4 ± 135.3 | 201.2 ± 55.9 | 766.0 ± 134.4 | 41.6 ± 6.0 | 2290 ± 131 | 1247 ± 228 | 3990 ± 535 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 279.6 ± 36.7 | 359.9 ± 38.6 | 182.4 ± 12.3 | 18.9 ± 2.7 | 427.2 ± 39.8 |
| Plan fix (Webster) | 234.2 ± 24.6 | 310.2 ± 27.4 | 175.6 ± 4.3 (-4%) | 17.0 ± 2.6 | 426.9 ± 15.4 (-0%) |
| Actuated SUMO | 375.6 ± 80.8 | 454.6 ± 83.8 | 236.6 ± 16.6 (+30%) | 31.9 ± 4.4 | 553.4 ± 58.3 (+30%) |
| Max-Pressure | 531.4 ± 118.8 | 619.7 ± 123.4 | 178.7 ± 13.7 (-2%) | 19.0 ± 2.8 | 447.6 ± 51.8 (+5%) |
| Agent RL (PPO) | 473.1 ± 100.3 | 555.6 ± 105.0 | 184.6 ± 19.3 (+1%) | 21.1 ± 7.0 | 430.1 ± 62.8 (+1%) |
| Agent RL v2 (cozi în amonte) | 418.1 ± 142.9 | 501.1 ± 150.0 | 237.2 ± 28.5 (+30%) | 35.5 ± 11.3 | 491.6 ± 86.5 (+15%) |
| Agent RL v3 (imitație + PPO) | 319.0 ± 90.7 | 398.4 ± 95.0 | 193.0 ± 39.5 (+6%) | 19.3 ± 1.5 | 455.6 ± 84.0 (+7%) |
| Agent RL coridor (piață + 4 vecini) | 583.4 ± 141.7 | 702.2 ± 151.0 | 186.6 ± 21.8 (+2%) | 15.9 ± 1.6 | 801.9 ± 85.5 (+88%) |

## Scenariul `zi_2026-10-22_dimineata`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 122.8 ± 10.1 | 120.1 | 181.9 ± 11.7 | 145.2 ± 13.4 | 303.7 ± 12.0 | 20.3 ± 1.5 | 2190 ± 17 | 269 ± 16 | 1661 ± 33 |
| Plan fix (Webster) | 117.0 ± 10.9 (-5%) | 117.4 (-2%) | 177.6 ± 13.5 | 130.8 ± 21.9 | 298.6 ± 13.3 | 20.5 ± 1.3 | 2250 ± 20 | 212 ± 19 | 1692 ± 52 |
| Actuated SUMO | 139.8 ± 11.9 (+14%) | 131.3 (+9%) | 201.7 ± 12.1 | 104.1 ± 3.0 | 322.4 ± 12.1 | 29.3 ± 1.8 | 2245 ± 27 | 243 ± 48 | 1779 ± 36 |
| Max-Pressure | 110.9 ± 11.4 (-10%) | 117.5 (-2%) | 174.3 ± 13.7 | 158.0 ± 16.0 | 295.6 ± 13.8 | 21.1 ± 1.7 | 2212 ± 14 | 240 ± 15 | 1675 ± 40 |
| Agent RL (PPO) | 104.8 ± 17.0 (-15%) | 95.4 (-21%) | 164.8 ± 20.0 | 153.2 ± 13.4 | 285.9 ± 20.0 | 17.1 ± 2.1 | 2220 ± 21 | 268 ± 73 | 1644 ± 59 |
| Agent RL coridor (piață + 4 vecini) | 339.3 ± 20.2 (+176%) | 335.2 (+179%) | 432.2 ± 25.0 | 195.5 ± 20.1 | 546.0 ± 24.9 | 15.2 ± 0.5 | 1967 ± 32 | 534 ± 117 | 2446 ± 67 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 180.3 ± 27.8 | 234.5 ± 30.1 | 158.9 ± 6.5 | 14.0 ± 1.7 | 301.4 ± 10.8 |
| Plan fix (Webster) | 146.5 ± 22.7 | 199.7 ± 23.1 | 149.6 ± 18.1 (-6%) | 12.5 ± 6.4 | 289.6 ± 28.2 (-4%) |
| Actuated SUMO | 172.1 ± 59.2 | 221.6 ± 63.8 | 211.7 ± 20.9 (+33%) | 27.3 ± 4.4 | 326.7 ± 16.7 (+8%) |
| Max-Pressure | 131.2 ± 43.7 | 183.3 ± 48.4 | 143.6 ± 12.3 (-10%) | 9.4 ± 0.5 | 297.7 ± 21.7 (-1%) |
| Agent RL (PPO) | 151.8 ± 42.5 | 206.7 ± 48.7 | 162.9 ± 34.2 (+2%) | 12.0 ± 0.9 | 301.8 ± 38.6 (+0%) |
| Agent RL coridor (piață + 4 vecini) | 333.7 ± 23.2 | 401.9 ± 23.2 | 149.1 ± 5.1 (-6%) | 9.6 ± 0.2 | 475.6 ± 22.4 (+58%) |

## Scenariul `zi_2026-10-22_linistit`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 53.5 ± 1.7 | 53.9 | 94.3 ± 1.7 | 0.5 ± 0.0 | 229.8 ± 2.1 | 1.2 ± 0.0 | 297 ± 0 | 0 ± 0 | 220 ± 1 |
| Plan fix (Webster) | 49.9 ± 0.6 (-7%) | 49.9 (-7%) | 91.1 ± 1.1 | 0.5 ± 0.0 | 226.6 ± 1.3 | 0.9 ± 0.0 | 297 ± 0 | 0 ± 0 | 219 ± 2 |
| Actuated SUMO | 47.8 ± 2.1 (-11%) | 48.3 (-10%) | 88.8 ± 3.2 | 0.5 ± 0.0 | 224.3 ± 3.3 | 0.7 ± 0.0 | 297 ± 0 | 0 ± 0 | 217 ± 3 |
| Max-Pressure | 42.1 ± 0.7 (-21%) | 42.4 (-21%) | 80.5 ± 1.7 | 0.5 ± 0.0 | 216.0 ± 1.9 | 0.4 ± 0.0 | 297 ± 0 | 1 ± 1 | 211 ± 2 |
| Agent RL (PPO) | 46.9 ± 2.3 (-12%) | 46.6 (-13%) | 88.1 ± 2.4 | 0.5 ± 0.0 | 223.6 ± 2.1 | 0.8 ± 0.1 | 297 ± 0 | 0 ± 0 | 219 ± 2 |
| Agent RL coridor (piață + 4 vecini) | 43.2 ± 1.3 (-19%) | 43.1 (-20%) | 82.6 ± 1.8 | 0.5 ± 0.0 | 218.1 ± 1.5 | 0.5 ± 0.0 | 297 ± 0 | 1 ± 0 | 213 ± 2 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 148.3 ± 4.0 | 0.1 ± 0.0 | 8.6 ± 0.2 |
| Plan fix (Webster) | nan ± nan | nan ± nan | 120.2 ± 6.0 (-19%) | 0.1 ± 0.0 | 8.2 ± 0.1 (-5%) |
| Actuated SUMO | nan ± nan | nan ± nan | 130.9 ± 6.6 (-12%) | 0.1 ± 0.0 | 8.1 ± 0.3 (-6%) |
| Max-Pressure | nan ± nan | nan ± nan | 220.4 ± 15.0 (+49%) | 0.1 ± 0.0 | 7.8 ± 0.2 (-9%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 123.5 ± 9.6 (-17%) | 0.1 ± 0.0 | 8.0 ± 0.2 (-7%) |
| Agent RL coridor (piață + 4 vecini) | nan ± nan | nan ± nan | 433.9 ± 60.2 (+193%) | 0.9 ± 0.2 | 9.1 ± 0.3 (+6%) |

## Scenariul `zi_2026-10-22_linistit_x0_8`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 53.1 ± 1.2 | 53.0 | 92.7 ± 1.3 | 0.5 ± 0.0 | 227.7 ± 1.7 | 1.0 ± 0.1 | 241 ± 0 | 0 ± 1 | 180 ± 1 |
| Plan fix (Webster) | 48.6 ± 0.9 (-8%) | 48.4 (-9%) | 88.8 ± 1.8 | 0.5 ± 0.0 | 223.8 ± 1.9 | 0.7 ± 0.0 | 241 ± 0 | 0 ± 1 | 180 ± 1 |
| Actuated SUMO | 46.4 ± 0.8 (-13%) | 46.5 (-12%) | 86.1 ± 0.5 | 0.5 ± 0.0 | 221.1 ± 0.6 | 0.6 ± 0.0 | 241 ± 0 | 0 ± 1 | 178 ± 1 |
| Max-Pressure | 42.0 ± 1.2 (-21%) | 42.2 (-20%) | 79.2 ± 1.6 | 0.5 ± 0.0 | 214.2 ± 1.6 | 0.3 ± 0.0 | 241 ± 0 | 1 ± 1 | 173 ± 1 |
| Agent RL (PPO) | 46.1 ± 0.7 (-13%) | 45.7 (-14%) | 85.4 ± 0.9 | 0.5 ± 0.0 | 220.4 ± 0.6 | 0.7 ± 0.0 | 241 ± 0 | 0 ± 1 | 180 ± 1 |
| Agent RL coridor (piață + 4 vecini) | 43.6 ± 1.5 (-18%) | 43.0 (-19%) | 81.3 ± 2.2 | 0.5 ± 0.0 | 216.3 ± 2.1 | 0.4 ± 0.0 | 241 ± 0 | 3 ± 1 | 175 ± 2 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 166.3 ± 6.2 | 0.1 ± 0.0 | 7.1 ± 0.1 |
| Plan fix (Webster) | nan ± nan | nan ± nan | 132.5 ± 7.1 (-20%) | 0.1 ± 0.0 | 6.7 ± 0.1 (-6%) |
| Actuated SUMO | nan ± nan | nan ± nan | 141.6 ± 6.0 (-15%) | 0.1 ± 0.0 | 6.5 ± 0.0 (-8%) |
| Max-Pressure | nan ± nan | nan ± nan | 240.4 ± 34.9 (+45%) | 0.1 ± 0.0 | 6.6 ± 0.2 (-7%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 139.3 ± 6.2 (-16%) | 0.1 ± 0.0 | 6.5 ± 0.1 (-9%) |
| Agent RL coridor (piață + 4 vecini) | nan ± nan | nan ± nan | 320.7 ± 87.2 (+93%) | 0.5 ± 0.2 | 7.2 ± 0.5 (+1%) |

## Scenariul `zi_2026-10-22_varf`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 179.4 ± 32.8 | 164.1 | 250.7 ± 35.8 | 103.4 ± 6.7 | 375.0 ± 35.6 | 32.4 ± 3.4 | 2384 ± 45 | 435 ± 73 | 2118 ± 116 |
| Plan fix (Webster) | 186.4 ± 38.6 (+4%) | 184.8 (+13%) | 261.6 ± 44.6 | 119.3 ± 13.3 | 385.6 ± 44.7 | 34.1 ± 4.9 | 2401 ± 41 | 449 ± 100 | 2187 ± 155 |
| Actuated SUMO | 324.6 ± 43.1 (+81%) | 310.0 (+89%) | 414.1 ± 47.4 | 107.6 ± 10.6 | 532.9 ± 46.8 | 43.3 ± 3.5 | 2345 ± 74 | 505 ± 102 | 2839 ± 142 |
| Max-Pressure | 241.8 ± 88.4 (+35%) | 213.3 (+30%) | 321.3 ± 90.8 | 66.8 ± 19.8 | 444.2 ± 88.2 | 37.0 ± 5.7 | 2259 ± 172 | 599 ± 249 | 2342 ± 267 |
| Agent RL (PPO) | 172.0 ± 35.0 (-4%) | 166.9 (+2%) | 244.2 ± 39.0 | 86.9 ± 23.2 | 368.5 ± 38.7 | 30.4 ± 3.5 | 2357 ± 48 | 471 ± 81 | 2097 ± 125 |
| Agent RL coridor (piață + 4 vecini) | 358.4 ± 20.5 (+100%) | 355.1 (+116%) | 458.2 ± 24.1 | 211.0 ± 15.0 | 573.6 ± 24.0 | 20.2 ± 3.5 | 2115 ± 41 | 672 ± 40 | 2742 ± 129 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 193.9 ± 25.9 | 254.7 ± 31.3 | 164.1 ± 13.7 | 14.1 ± 1.5 | 339.0 ± 28.9 |
| Plan fix (Webster) | 188.5 ± 54.5 | 246.0 ± 58.4 | 181.3 ± 40.0 (+10%) | 12.5 ± 3.2 | 370.1 ± 43.5 (+9%) |
| Actuated SUMO | 308.6 ± 113.2 | 368.2 ± 116.6 | 201.9 ± 10.5 (+23%) | 25.6 ± 1.8 | 492.7 ± 37.4 (+45%) |
| Max-Pressure | 383.4 ± 144.9 | 445.3 ± 145.8 | 165.4 ± 29.8 (+1%) | 12.9 ± 2.5 | 357.9 ± 60.9 (+6%) |
| Agent RL (PPO) | 256.9 ± 31.9 | 316.0 ± 32.8 | 167.9 ± 29.3 (+2%) | 13.3 ± 1.5 | 324.9 ± 33.9 (-4%) |
| Agent RL coridor (piață + 4 vecini) | 298.5 ± 77.9 | 363.2 ± 80.0 | 144.1 ± 1.7 (-12%) | 10.0 ± 0.5 | 526.2 ± 20.6 (+55%) |

## Scenariul `zi_2026-10-22_varf_x1_2`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 247.7 ± 46.9 | 215.5 | 339.0 ± 56.0 | 121.5 ± 11.6 | 463.5 ± 55.7 | 39.4 ± 4.5 | 2705 ± 49 | 676 ± 91 | 2872 ± 232 |
| Plan fix (Webster) | 287.0 ± 43.8 (+16%) | 311.6 (+45%) | 383.2 ± 47.9 | 121.9 ± 13.2 | 505.7 ± 47.1 | 44.8 ± 3.9 | 2726 ± 86 | 721 ± 133 | 3127 ± 186 |
| Actuated SUMO | 351.7 ± 52.9 (+42%) | 332.0 (+54%) | 447.9 ± 56.1 | 173.2 ± 16.9 | 562.6 ± 56.3 | 45.2 ± 5.6 | 2597 ± 79 | 817 ± 110 | 3398 ± 171 |
| Max-Pressure | 296.3 ± 87.8 (+20%) | 273.3 (+27%) | 394.0 ± 90.5 | 74.7 ± 5.7 | 515.7 ± 86.4 | 40.4 ± 5.0 | 2545 ± 186 | 873 ± 243 | 3041 ± 311 |
| Agent RL (PPO) | 250.6 ± 28.1 (+1%) | 246.4 (+14%) | 349.6 ± 32.0 | 104.5 ± 14.1 | 474.0 ± 31.5 | 39.4 ± 2.9 | 2678 ± 51 | 687 ± 41 | 2910 ± 133 |
| Agent RL coridor (piață + 4 vecini) | 385.0 ± 27.9 (+55%) | 386.2 (+79%) | 498.9 ± 33.1 | 279.2 ± 11.8 | 616.1 ± 33.6 | 24.7 ± 5.9 | 2335 ± 47 | 1034 ± 68 | 3216 ± 149 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 210.7 ± 30.7 | 273.6 ± 34.8 | 166.4 ± 9.6 | 16.8 ± 2.7 | 462.8 ± 49.3 |
| Plan fix (Webster) | 211.3 ± 37.0 | 275.3 ± 38.7 | 189.5 ± 25.8 (+14%) | 17.0 ± 3.7 | 521.5 ± 43.9 (+13%) |
| Actuated SUMO | 281.1 ± 54.9 | 346.5 ± 60.3 | 215.7 ± 26.8 (+30%) | 29.5 ± 6.4 | 641.9 ± 61.2 (+39%) |
| Max-Pressure | 332.1 ± 115.2 | 397.7 ± 116.2 | 184.5 ± 25.6 (+11%) | 15.5 ± 2.5 | 474.0 ± 74.5 (+2%) |
| Agent RL (PPO) | 289.0 ± 76.3 | 359.5 ± 82.5 | 165.7 ± 11.7 (-0%) | 15.1 ± 1.6 | 455.0 ± 30.3 (-2%) |
| Agent RL coridor (piață + 4 vecini) | 318.1 ± 43.5 | 388.7 ± 45.7 | 156.0 ± 9.7 (-6%) | 11.9 ± 0.8 | 659.3 ± 29.5 (+42%) |
