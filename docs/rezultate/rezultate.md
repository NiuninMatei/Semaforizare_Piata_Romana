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

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 34.0 ± 5.9 | 65.8 ± 4.5 | 154.0 ± 1.2 | 12.3 ± 0.2 | 112.1 ± 0.5 |
| Plan fix (Webster) | 193.7 ± 122.8 | 252.1 ± 142.6 | 134.1 ± 4.7 (-13%) | 7.0 ± 0.5 | 120.5 ± 17.2 (+7%) |
| Actuated SUMO | 47.4 ± 24.2 | 79.9 ± 25.7 | 146.7 ± 4.3 (-5%) | 10.2 ± 0.7 | 107.9 ± 4.4 (-4%) |
| Max-Pressure | 58.4 ± 25.1 | 95.8 ± 25.1 | 124.0 ± 1.4 (-19%) | 5.5 ± 0.3 | 101.1 ± 6.8 (-10%) |
| Agent RL (PPO) | 49.7 ± 13.3 | 88.2 ± 18.8 | 139.8 ± 19.2 (-9%) | 7.6 ± 2.4 | 106.7 ± 9.5 (-5%) |

## Scenariul `zi_2026-10-21_linistit_x0_8`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 44.4 ± 0.7 | 44.2 | 82.1 ± 0.8 | 4.1 ± 0.3 | 206.9 ± 0.8 | 3.1 ± 0.2 | 859 ± 0 | 70 ± 3 | 549 ± 2 |
| Plan fix (Webster) | 51.7 ± 8.8 (+16%) | 48.7 (+10%) | 91.5 ± 10.0 | 5.0 ± 0.6 | 216.2 ± 10.0 | 4.2 ± 0.9 | 859 ± 0 | 76 ± 23 | 569 ± 15 |
| Actuated SUMO | 45.6 ± 6.8 (+3%) | 41.3 (-7%) | 83.2 ± 7.1 | 5.7 ± 1.8 | 207.9 ± 7.2 | 2.9 ± 0.5 | 859 ± 0 | 61 ± 2 | 550 ± 9 |
| Max-Pressure | 54.6 ± 7.7 (+23%) | 51.8 (+17%) | 95.3 ± 8.3 | 3.6 ± 0.7 | 220.0 ± 8.4 | 4.2 ± 0.8 | 859 ± 0 | 57 ± 4 | 578 ± 12 |
| Agent RL (PPO) | 49.4 ± 5.5 (+11%) | 50.3 (+14%) | 88.4 ± 5.5 | 3.7 ± 0.4 | 213.1 ± 5.5 | 3.1 ± 0.5 | 859 ± 0 | 62 ± 5 | 565 ± 6 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 13.6 ± 13.6 | 28.2 ± 15.7 | 153.1 ± 1.2 | 11.6 ± 0.2 | 105.1 ± 0.6 |
| Plan fix (Webster) | 40.0 ± 5.6 | 59.4 ± 5.4 | 139.8 ± 16.9 (-9%) | 10.3 ± 6.8 | 100.2 ± 9.1 (-5%) |
| Actuated SUMO | 27.2 ± 20.0 | 45.3 ± 23.9 | 142.2 ± 4.3 (-7%) | 8.9 ± 0.8 | 99.8 ± 3.7 (-5%) |
| Max-Pressure | 36.8 ± 5.6 | 58.6 ± 5.2 | 121.3 ± 1.4 (-21%) | 4.6 ± 0.4 | 90.6 ± 2.6 (-14%) |
| Agent RL (PPO) | 21.2 ± 15.1 | 39.1 ± 15.2 | 124.7 ± 0.6 (-19%) | 5.5 ± 0.3 | 90.9 ± 1.5 (-14%) |

## Scenariul `zi_2026-10-21_pranz`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 111.0 ± 8.2 | 106.5 | 165.7 ± 9.1 | 108.4 ± 6.2 | 283.8 ± 9.3 | 18.4 ± 1.1 | 1908 ± 20 | 144 ± 23 | 1402 ± 21 |
| Plan fix (Webster) | 106.0 ± 9.4 (-5%) | 104.0 (-2%) | 160.3 ± 10.4 | 109.1 ± 14.0 | 278.3 ± 10.5 | 17.3 ± 1.3 | 1894 ± 30 | 189 ± 91 | 1379 ± 25 |
| Actuated SUMO | 118.5 ± 19.5 (+7%) | 121.8 (+14%) | 175.0 ± 21.7 | 38.1 ± 12.8 | 293.5 ± 21.7 | 22.0 ± 3.2 | 1949 ± 0 | 165 ± 68 | 1455 ± 71 |
| Max-Pressure | 121.4 ± 16.4 (+9%) | 127.8 (+20%) | 182.2 ± 19.4 | 136.9 ± 9.8 | 300.2 ± 19.3 | 20.6 ± 2.2 | 1879 ± 24 | 166 ± 19 | 1456 ± 50 |
| Agent RL (PPO) | 91.5 ± 7.5 (-18%) | 87.8 (-17%) | 146.2 ± 8.0 | 120.3 ± 21.2 | 264.4 ± 7.9 | 14.3 ± 1.3 | 1923 ± 25 | 126 ± 26 | 1356 ± 16 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 149.4 ± 9.3 | 198.7 ± 10.8 | 153.6 ± 2.0 | 13.3 ± 0.5 | 244.0 ± 8.5 |
| Plan fix (Webster) | 154.9 ± 7.3 | 209.2 ± 7.6 | 148.7 ± 29.0 (-3%) | 8.9 ± 0.3 | 237.8 ± 29.3 (-3%) |
| Actuated SUMO | 94.3 ± 20.1 | 134.6 ± 23.6 | 222.7 ± 32.8 (+45%) | 26.0 ± 4.4 | 255.3 ± 14.2 (+5%) |
| Max-Pressure | 204.8 ± 75.3 | 264.5 ± 80.5 | 136.3 ± 4.6 (-11%) | 9.2 ± 0.8 | 256.0 ± 15.5 (+5%) |
| Agent RL (PPO) | 130.8 ± 15.6 | 182.9 ± 17.5 | 140.7 ± 3.4 (-8%) | 10.7 ± 1.0 | 232.3 ± 15.2 (-5%) |

## Scenariul `zi_2026-10-21_varf`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 135.4 ± 16.1 | 126.0 | 198.9 ± 17.6 | 104.9 ± 4.5 | 323.8 ± 18.0 | 28.8 ± 2.5 | 2404 ± 15 | 498 ± 171 | 1838 ± 62 |
| Plan fix (Webster) | 203.8 ± 70.7 (+51%) | 186.0 (+48%) | 273.9 ± 74.5 | 111.7 ± 10.4 | 395.5 ± 72.0 | 38.8 ± 7.7 | 2355 ± 114 | 520 ± 183 | 2141 ± 259 |
| Actuated SUMO | 231.8 ± 35.1 (+71%) | 221.8 (+76%) | 306.2 ± 39.7 | 78.8 ± 10.5 | 428.5 ± 39.2 | 44.2 ± 3.7 | 2442 ± 39 | 447 ± 106 | 2326 ± 146 |
| Max-Pressure | 172.2 ± 17.8 (+27%) | 176.7 (+40%) | 246.3 ± 21.9 | 86.1 ± 15.6 | 370.9 ± 22.1 | 34.6 ± 2.9 | 2282 ± 37 | 653 ± 178 | 1958 ± 82 |
| Agent RL (PPO) | 143.5 ± 35.3 (+6%) | 124.1 (-2%) | 211.0 ± 38.6 | 96.6 ± 29.3 | 336.3 ± 39.2 | 28.6 ± 5.6 | 2333 ± 44 | 523 ± 58 | 1840 ± 123 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 230.9 ± 34.1 | 299.4 ± 36.2 | 187.6 ± 35.9 | 20.2 ± 3.9 | 335.7 ± 27.4 |
| Plan fix (Webster) | 226.1 ± 54.9 | 297.3 ± 60.6 | 178.5 ± 16.0 (-5%) | 15.8 ± 3.3 | 389.7 ± 58.3 (+16%) |
| Actuated SUMO | 257.1 ± 78.7 | 322.6 ± 84.7 | 227.3 ± 15.4 (+21%) | 32.1 ± 3.7 | 428.0 ± 34.1 (+28%) |
| Max-Pressure | 397.6 ± 60.5 | 477.4 ± 63.0 | 183.1 ± 34.0 (-2%) | 14.1 ± 1.2 | 346.3 ± 38.8 (+3%) |
| Agent RL (PPO) | 326.8 ± 78.3 | 399.2 ± 78.1 | 178.0 ± 21.0 (-5%) | 16.6 ± 3.1 | 327.9 ± 27.8 (-2%) |

## Scenariul `zi_2026-10-21_varf_x1_2`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 206.6 ± 39.9 | 195.0 | 284.1 ± 46.6 | 94.4 ± 11.6 | 409.2 ± 46.4 | 43.6 ± 4.7 | 2791 ± 29 | 572 ± 55 | 2537 ± 211 |
| Plan fix (Webster) | 212.2 ± 16.3 (+3%) | 216.5 (+11%) | 288.9 ± 18.6 | 87.0 ± 10.9 | 411.8 ± 18.7 | 46.5 ± 2.6 | 2792 ± 33 | 572 ± 54 | 2599 ± 88 |
| Actuated SUMO | 307.5 ± 53.4 (+49%) | 289.5 (+48%) | 404.0 ± 59.6 | 66.2 ± 11.8 | 525.9 ± 59.0 | 51.0 ± 3.7 | 2808 ± 71 | 631 ± 52 | 3168 ± 240 |
| Max-Pressure | 276.1 ± 69.8 (+34%) | 267.7 (+37%) | 364.6 ± 75.5 | 55.9 ± 16.2 | 487.5 ± 73.7 | 49.6 ± 6.8 | 2551 ± 145 | 894 ± 193 | 2752 ± 255 |
| Agent RL (PPO) | 232.4 ± 64.1 (+13%) | 237.8 (+22%) | 319.0 ± 74.3 | 71.4 ± 21.5 | 444.2 ± 72.6 | 41.6 ± 5.2 | 2648 ± 128 | 809 ± 281 | 2578 ± 282 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 279.6 ± 36.7 | 359.9 ± 38.6 | 182.4 ± 12.3 | 18.9 ± 2.7 | 427.2 ± 39.8 |
| Plan fix (Webster) | 234.2 ± 24.6 | 310.2 ± 27.4 | 175.6 ± 4.3 (-4%) | 17.0 ± 2.6 | 426.9 ± 15.4 (-0%) |
| Actuated SUMO | 375.6 ± 80.8 | 454.6 ± 83.8 | 236.6 ± 16.6 (+30%) | 31.9 ± 4.4 | 553.4 ± 58.3 (+30%) |
| Max-Pressure | 531.4 ± 118.8 | 619.7 ± 123.4 | 178.7 ± 13.7 (-2%) | 19.0 ± 2.8 | 447.6 ± 51.8 (+5%) |
| Agent RL (PPO) | 473.1 ± 100.3 | 555.6 ± 105.0 | 184.6 ± 19.3 (+1%) | 21.1 ± 7.0 | 430.1 ± 62.8 (+1%) |
