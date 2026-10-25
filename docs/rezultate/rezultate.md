# Rezultate – evaluare comparativă

Medii ± abatere standard pe 5 seed-uri SUMO. Procentele sunt față de plan fix de referință. Mediana pe seed-uri este dată separat pentru așteptarea vehiculelor: aproape de saturație, rețeaua poate intra sau nu în blocaj în funcție de seed, iar câteva rulări blocate trag media în sus. Generat automat de `python -m romana.control.evaluate`.


## Scenariul `zi_2026-10-21_linistit`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 45.0 ± 0.6 | 45.2 | 83.5 ± 0.6 | 1.4 ± 0.1 | 206.8 ± 0.3 | 3.7 ± 0.2 | 896 ± 0 | 13 ± 3 | 490 ± 1 |
| Plan fix (Webster) | 42.9 ± 1.5 (-5%) | 42.5 (-6%) | 82.0 ± 1.6 | 1.1 ± 0.3 | 205.3 ± 1.6 | 3.3 ± 0.2 | 896 ± 0 | 12 ± 2 | 491 ± 3 |
| Actuated SUMO | 40.7 ± 1.7 (-9%) | 41.0 (-9%) | 79.2 ± 2.1 | 1.0 ± 0.1 | 202.5 ± 1.7 | 2.9 ± 0.2 | 896 ± 0 | 12 ± 2 | 485 ± 3 |
| Max-Pressure | 37.6 ± 0.6 (-16%) | 37.3 (-17%) | 76.3 ± 0.9 | 1.6 ± 0.5 | 199.5 ± 1.1 | 2.2 ± 0.2 | 896 ± 0 | 14 ± 2 | 483 ± 2 |
| Agent RL (PPO) | 40.5 ± 0.6 (-10%) | 40.5 (-10%) | 79.8 ± 0.7 | 1.1 ± 0.1 | 203.0 ± 1.2 | 2.5 ± 0.1 | 896 ± 0 | 13 ± 2 | 489 ± 2 |
| plan_46_48_12 | 50.8 ± 1.0 (+13%) | 50.8 (+12%) | 90.1 ± 1.5 | 1.1 ± 0.2 | 213.4 ± 1.1 | 4.9 ± 0.1 | 896 ± 0 | 15 ± 3 | 500 ± 4 |
| rl_ppo_romana_greu_bc | 51.5 ± 2.5 (+15%) | 50.5 (+12%) | 90.7 ± 3.3 | 1.6 ± 0.3 | 213.9 ± 3.4 | 5.1 ± 0.3 | 896 ± 0 | 15 ± 2 | 500 ± 5 |
| rl_ppo_romana_greu_e7_400k | 48.8 ± 1.1 (+9%) | 48.9 (+8%) | 87.6 ± 1.5 | 1.7 ± 0.3 | 210.9 ± 1.4 | 4.7 ± 0.1 | 896 ± 0 | 16 ± 2 | 496 ± 3 |
| rl_ppo_romana_zn3 | 32.5 ± 1.1 (-28%) | 32.5 (-28%) | 69.7 ± 1.4 | 2.3 ± 0.7 | 193.0 ± 1.7 | 1.4 ± 0.1 | 896 ± 0 | 14 ± 2 | 472 ± 2 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 135.6 ± 2.4 | 1.2 ± 0.1 | 30.4 ± 0.2 |
| Plan fix (Webster) | nan ± nan | nan ± nan | 115.3 ± 2.1 (-15%) | 0.6 ± 0.1 | 28.6 ± 0.5 (-6%) |
| Actuated SUMO | nan ± nan | nan ± nan | 128.2 ± 1.9 (-5%) | 0.9 ± 0.1 | 28.8 ± 0.5 (-5%) |
| Max-Pressure | nan ± nan | nan ± nan | 127.6 ± 6.2 (-6%) | 0.8 ± 0.2 | 28.1 ± 0.5 (-8%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 116.5 ± 1.3 (-14%) | 0.7 ± 0.0 | 28.1 ± 0.1 (-8%) |
| plan_46_48_12 | nan ± nan | nan ± nan | 150.3 ± 3.0 (+11%) | 1.7 ± 0.1 | 33.0 ± 0.4 (+9%) |
| rl_ppo_romana_greu_bc | nan ± nan | nan ± nan | 157.8 ± 1.6 (+16%) | 2.0 ± 0.1 | 33.8 ± 0.7 (+11%) |
| rl_ppo_romana_greu_e7_400k | nan ± nan | nan ± nan | 156.0 ± 2.9 (+15%) | 2.0 ± 0.0 | 32.9 ± 0.5 (+8%) |
| rl_ppo_romana_zn3 | nan ± nan | nan ± nan | 155.1 ± 4.6 (+14%) | 1.5 ± 0.1 | 28.6 ± 0.6 (-6%) |

## Scenariul `zi_2026-10-21_linistit_x0_8`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 45.4 ± 1.2 | 45.1 | 83.6 ± 1.5 | 1.3 ± 0.2 | 207.0 ± 1.6 | 3.1 ± 0.1 | 712 ± 0 | 9 ± 2 | 397 ± 2 |
| Plan fix (Webster) | 41.0 ± 0.7 (-10%) | 41.1 (-9%) | 78.8 ± 1.1 | 1.0 ± 0.2 | 202.2 ± 1.2 | 2.4 ± 0.1 | 712 ± 0 | 8 ± 2 | 392 ± 2 |
| Actuated SUMO | 38.2 ± 1.3 (-16%) | 38.3 (-15%) | 75.1 ± 1.3 | 1.1 ± 0.1 | 198.5 ± 1.5 | 2.1 ± 0.0 | 712 ± 0 | 9 ± 2 | 386 ± 2 |
| Max-Pressure | 38.1 ± 1.1 (-16%) | 38.5 (-15%) | 75.9 ± 1.5 | 1.2 ± 0.3 | 199.3 ± 1.7 | 1.6 ± 0.1 | 712 ± 0 | 9 ± 2 | 390 ± 3 |
| Agent RL (PPO) | 40.6 ± 0.9 (-11%) | 41.1 (-9%) | 78.9 ± 1.4 | 1.0 ± 0.1 | 202.3 ± 1.7 | 1.9 ± 0.1 | 712 ± 0 | 9 ± 2 | 394 ± 3 |
| plan_46_48_12 | 48.2 ± 1.2 (+6%) | 48.4 (+7%) | 86.1 ± 1.7 | 1.6 ± 0.3 | 209.5 ± 1.9 | 3.4 ± 0.1 | 712 ± 0 | 9 ± 2 | 399 ± 3 |
| rl_ppo_romana_greu_bc | 52.0 ± 0.8 (+14%) | 52.2 (+16%) | 90.7 ± 1.4 | 2.1 ± 0.5 | 214.1 ± 1.3 | 4.1 ± 0.1 | 712 ± 0 | 10 ± 2 | 405 ± 2 |
| rl_ppo_romana_greu_e7_400k | 50.0 ± 0.8 (+10%) | 50.1 (+11%) | 88.0 ± 1.6 | 2.0 ± 0.3 | 211.4 ± 1.7 | 3.9 ± 0.1 | 712 ± 0 | 10 ± 1 | 400 ± 4 |
| rl_ppo_romana_zn3 | 33.0 ± 1.8 (-27%) | 32.4 (-28%) | 69.4 ± 2.3 | 2.7 ± 0.7 | 192.8 ± 2.3 | 1.1 ± 0.1 | 712 ± 0 | 9 ± 2 | 380 ± 4 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 136.0 ± 2.0 | 1.3 ± 0.1 | 26.1 ± 0.4 |
| Plan fix (Webster) | nan ± nan | nan ± nan | 114.8 ± 0.5 (-16%) | 0.6 ± 0.0 | 23.7 ± 0.2 (-9%) |
| Actuated SUMO | nan ± nan | nan ± nan | 124.4 ± 1.9 (-8%) | 0.9 ± 0.1 | 23.6 ± 0.3 (-10%) |
| Max-Pressure | nan ± nan | nan ± nan | 123.6 ± 2.6 (-9%) | 0.7 ± 0.0 | 23.7 ± 0.1 (-9%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 116.9 ± 1.7 (-14%) | 0.8 ± 0.1 | 23.8 ± 0.3 (-9%) |
| plan_46_48_12 | nan ± nan | nan ± nan | 152.6 ± 1.6 (+12%) | 1.8 ± 0.1 | 27.8 ± 0.3 (+7%) |
| rl_ppo_romana_greu_bc | nan ± nan | nan ± nan | 157.9 ± 1.7 (+16%) | 2.2 ± 0.1 | 29.2 ± 0.2 (+12%) |
| rl_ppo_romana_greu_e7_400k | nan ± nan | nan ± nan | 157.9 ± 1.9 (+16%) | 2.3 ± 0.1 | 28.6 ± 0.4 (+10%) |
| rl_ppo_romana_zn3 | nan ± nan | nan ± nan | 146.5 ± 4.4 (+8%) | 1.4 ± 0.1 | 24.3 ± 0.4 (-7%) |

## Scenariul `zi_2026-10-21_pranz`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 86.6 ± 19.3 | 83.0 | 140.0 ± 23.5 | 69.5 ± 12.3 | 261.4 ± 24.5 | 10.6 ± 0.5 | 1854 ± 43 | 403 ± 144 | 1333 ± 52 |
| Plan fix (Webster) | 148.4 ± 40.7 (+71%) | 156.8 (+89%) | 212.4 ± 46.5 | 68.0 ± 9.2 | 332.2 ± 46.0 | 20.8 ± 2.8 | 1831 ± 47 | 448 ± 124 | 1559 ± 128 |
| Actuated SUMO | 74.2 ± 12.9 (-14%) | 77.6 (-7%) | 125.0 ± 16.5 | 61.4 ± 6.2 | 245.9 ± 16.8 | 12.3 ± 2.2 | 1899 ± 9 | 566 ± 150 | 1303 ± 49 |
| Max-Pressure | 314.9 ± 64.4 (+263%) | 307.7 (+271%) | 388.0 ± 61.2 | 33.6 ± 6.3 | 503.8 ± 60.5 | 27.1 ± 4.2 | 1586 ± 98 | 702 ± 192 | 1971 ± 124 |
| Agent RL (PPO) | 141.2 ± 21.0 (+63%) | 146.4 (+76%) | 211.9 ± 25.9 | 70.5 ± 14.6 | 333.7 ± 25.8 | 12.5 ± 1.4 | 1828 ± 27 | 227 ± 40 | 1549 ± 75 |
| plan_46_48_12 | 79.0 ± 16.7 (-9%) | 83.2 (+0%) | 129.5 ± 20.4 | 72.1 ± 10.7 | 250.4 ± 20.8 | 12.9 ± 2.3 | 1877 ± 20 | 352 ± 145 | 1309 ± 62 |
| rl_ppo_romana_greu_bc | 70.5 ± 11.3 (-19%) | 73.7 (-11%) | 120.0 ± 14.2 | 91.7 ± 11.9 | 240.8 ± 14.1 | 10.9 ± 0.6 | 1862 ± 13 | 288 ± 78 | 1279 ± 43 |
| rl_ppo_romana_greu_e7_400k | 86.1 ± 11.4 (-1%) | 86.6 (+4%) | 139.8 ± 15.2 | 87.0 ± 16.5 | 261.0 ± 15.0 | 12.5 ± 1.7 | 1850 ± 10 | 343 ± 181 | 1333 ± 48 |
| rl_ppo_romana_zn3 | 106.8 ± 36.2 (+23%) | 109.6 (+32%) | 167.9 ± 43.4 | 77.5 ± 15.1 | 289.1 ± 43.6 | 10.5 ± 1.7 | 1839 ± 31 | 274 ± 132 | 1420 ± 118 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 47.6 ± 7.8 | 80.7 ± 8.4 | 206.2 ± 31.9 | 25.3 ± 2.4 | 289.6 ± 35.2 |
| Plan fix (Webster) | 68.4 ± 21.4 | 106.2 ± 22.6 | 200.2 ± 47.5 (-3%) | 14.8 ± 1.4 | 322.2 ± 59.8 (+11%) |
| Actuated SUMO | 66.2 ± 21.8 | 101.1 ± 25.1 | 274.1 ± 23.3 (+33%) | 32.0 ± 4.4 | 338.8 ± 24.8 (+17%) |
| Max-Pressure | 115.8 ± 105.4 | 159.8 ± 110.6 | 165.6 ± 21.0 (-20%) | 16.9 ± 3.9 | 355.9 ± 39.7 (+23%) |
| Agent RL (PPO) | 55.9 ± 10.7 | 94.7 ± 12.3 | 137.5 ± 7.1 (-33%) | 12.3 ± 1.3 | 266.3 ± 20.0 (-8%) |
| plan_46_48_12 | 54.0 ± 12.0 | 87.6 ± 14.0 | 217.6 ± 50.2 (+6%) | 36.1 ± 4.0 | 296.7 ± 50.0 (+2%) |
| rl_ppo_romana_greu_bc | 54.5 ± 6.3 | 87.9 ± 6.6 | 193.0 ± 10.8 (-6%) | 34.9 ± 3.3 | 280.3 ± 15.7 (-3%) |
| rl_ppo_romana_greu_e7_400k | 63.7 ± 7.2 | 99.6 ± 7.6 | 209.2 ± 24.8 (+1%) | 36.5 ± 2.3 | 301.6 ± 19.1 (+4%) |
| rl_ppo_romana_zn3 | 52.0 ± 11.9 | 90.3 ± 13.2 | 159.2 ± 14.9 (-23%) | 18.4 ± 4.4 | 267.1 ± 29.2 (-8%) |

## Scenariul `zi_2026-10-21_varf`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 462.3 ± 60.7 | 440.9 | 579.0 ± 58.7 | 99.9 ± 16.0 | 692.0 ± 56.1 | 39.0 ± 1.8 | 2215 ± 133 | 1080 ± 138 | 3472 ± 123 |
| Plan fix (Webster) | 492.6 ± 55.4 (+7%) | 488.0 (+11%) | 595.9 ± 60.0 | 124.9 ± 25.1 | 709.0 ± 58.7 | 40.3 ± 3.1 | 2146 ± 102 | 1124 ± 193 | 3436 ± 164 |
| Actuated SUMO | 420.2 ± 74.3 (-9%) | 420.9 (-5%) | 505.0 ± 74.3 | 83.3 ± 34.7 | 619.2 ± 71.4 | 39.2 ± 2.8 | 2201 ± 144 | 1321 ± 179 | 3119 ± 179 |
| Max-Pressure | 829.7 ± 162.2 (+79%) | 776.5 (+76%) | 938.0 ± 153.2 | 112.3 ± 32.5 | 1045.1 ± 152.9 | 51.1 ± 9.5 | 1619 ± 225 | 1720 ± 478 | 4163 ± 180 |
| Agent RL (PPO) | 721.4 ± 172.0 (+56%) | 696.6 (+58%) | 829.3 ± 158.4 | 99.0 ± 27.2 | 939.2 ± 155.6 | 48.4 ± 7.7 | 1798 ± 306 | 1919 ± 506 | 3958 ± 203 |
| plan_46_48_12 | 410.4 ± 54.8 (-11%) | 395.0 (-10%) | 512.6 ± 59.3 | 92.7 ± 18.1 | 628.7 ± 58.7 | 38.3 ± 2.1 | 2307 ± 106 | 1037 ± 365 | 3242 ± 151 |
| rl_ppo_romana_greu_bc | 502.9 ± 77.8 (+9%) | 503.7 (+14%) | 606.8 ± 82.3 | 127.8 ± 55.3 | 718.7 ± 79.1 | 40.2 ± 3.1 | 2141 ± 153 | 1240 ± 260 | 3497 ± 229 |
| rl_ppo_romana_greu_e7_400k | 482.9 ± 67.3 (+4%) | 440.6 (-0%) | 586.7 ± 59.3 | 87.2 ± 15.6 | 698.6 ± 56.3 | 38.7 ± 2.7 | 2153 ± 177 | 1269 ± 192 | 3479 ± 159 |
| rl_ppo_romana_zn3 | 633.4 ± 99.2 (+37%) | 584.4 (+33%) | 730.6 ± 95.7 | 63.4 ± 15.2 | 839.4 ± 93.1 | 44.1 ± 4.6 | 1827 ± 163 | 2044 ± 314 | 3701 ± 193 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 360.3 ± 76.2 | 428.9 ± 81.3 | 211.3 ± 15.9 | 21.8 ± 2.8 | 683.7 ± 44.9 |
| Plan fix (Webster) | 376.3 ± 71.9 | 448.6 ± 73.5 | 225.8 ± 20.9 (+7%) | 19.3 ± 3.9 | 713.0 ± 62.9 (+4%) |
| Actuated SUMO | 358.6 ± 104.4 | 426.8 ± 111.9 | 267.6 ± 18.9 (+27%) | 39.4 ± 6.3 | 659.3 ± 77.1 (-4%) |
| Max-Pressure | 815.0 ± 260.8 | 889.9 ± 258.1 | 224.7 ± 56.1 (+6%) | 23.8 ± 5.1 | 862.3 ± 110.4 (+26%) |
| Agent RL (PPO) | 717.1 ± 191.3 | 795.7 ± 189.0 | 312.6 ± 39.8 (+48%) | 79.8 ± 24.4 | 883.5 ± 91.1 (+29%) |
| plan_46_48_12 | 303.0 ± 62.1 | 364.5 ± 65.6 | 250.1 ± 45.0 (+18%) | 36.0 ± 1.6 | 665.7 ± 79.8 (-3%) |
| rl_ppo_romana_greu_bc | 347.7 ± 139.9 | 415.3 ± 144.1 | 261.4 ± 42.3 (+24%) | 34.3 ± 4.6 | 758.4 ± 123.4 (+11%) |
| rl_ppo_romana_greu_e7_400k | 352.0 ± 133.9 | 418.6 ± 131.2 | 257.2 ± 25.3 (+22%) | 32.2 ± 6.4 | 718.8 ± 44.1 (+5%) |
| rl_ppo_romana_zn3 | 730.5 ± 153.3 | 802.6 ± 161.6 | 289.1 ± 27.9 (+37%) | 96.6 ± 18.8 | 791.9 ± 74.6 (+16%) |

## Scenariul `zi_2026-10-21_varf_x1_2`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 581.2 ± 35.3 | 576.1 | 714.2 ± 32.8 | 204.3 ± 13.0 | 820.9 ± 31.8 | 43.9 ± 2.5 | 2317 ± 102 | 1585 ± 236 | 4419 ± 60 |
| Plan fix (Webster) | 570.9 ± 35.7 (-2%) | 558.7 (-3%) | 698.4 ± 38.6 | 155.4 ± 39.6 | 809.2 ± 38.5 | 46.9 ± 4.7 | 2305 ± 47 | 1446 ± 92 | 4212 ± 171 |
| Actuated SUMO | 516.9 ± 43.3 (-11%) | 541.5 (-6%) | 635.5 ± 42.1 | 99.7 ± 47.2 | 748.6 ± 40.9 | 45.2 ± 3.1 | 2387 ± 127 | 1690 ± 213 | 4023 ± 132 |
| Max-Pressure | 883.8 ± 75.5 (+52%) | 897.6 (+56%) | 1001.2 ± 64.9 | 247.8 ± 48.4 | 1107.7 ± 65.1 | 58.9 ± 4.8 | 1797 ± 142 | 2097 ± 273 | 4825 ± 51 |
| Agent RL (PPO) | 856.1 ± 137.2 (+47%) | 822.9 (+43%) | 963.0 ± 131.5 | 157.3 ± 95.5 | 1069.9 ± 130.6 | 58.2 ± 3.2 | 1800 ± 202 | 2615 ± 461 | 4748 ± 161 |
| plan_46_48_12 | 492.3 ± 29.6 (-15%) | 509.0 (-12%) | 619.9 ± 29.3 | 127.5 ± 14.7 | 732.7 ± 28.8 | 42.9 ± 3.0 | 2468 ± 95 | 1465 ± 173 | 4064 ± 49 |
| rl_ppo_romana_greu_bc | 511.2 ± 40.2 (-12%) | 500.5 (-13%) | 639.2 ± 39.8 | 145.6 ± 34.4 | 752.4 ± 37.2 | 43.2 ± 1.7 | 2462 ± 84 | 1461 ± 91 | 4144 ± 155 |
| rl_ppo_romana_greu_e7_400k | 491.9 ± 47.9 (-15%) | 479.9 (-17%) | 619.6 ± 48.1 | 130.6 ± 14.9 | 731.8 ± 46.0 | 41.6 ± 2.5 | 2490 ± 99 | 1391 ± 235 | 4125 ± 154 |
| rl_ppo_romana_zn3 | 811.2 ± 165.7 (+40%) | 791.0 (+37%) | 913.6 ± 161.3 | 109.5 ± 33.0 | 1021.0 ± 158.6 | 53.5 ± 6.1 | 1846 ± 268 | 2682 ± 420 | 4528 ± 168 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 357.7 ± 84.6 | 427.4 ± 86.3 | 241.8 ± 30.0 | 22.7 ± 4.0 | 962.1 ± 24.8 |
| Plan fix (Webster) | 380.7 ± 72.5 | 441.8 ± 79.1 | 226.9 ± 18.6 (-6%) | 25.4 ± 4.4 | 873.5 ± 39.0 (-9%) |
| Actuated SUMO | 386.7 ± 81.5 | 443.9 ± 76.8 | 293.0 ± 46.1 (+21%) | 47.7 ± 8.6 | 847.0 ± 68.2 (-12%) |
| Max-Pressure | 811.5 ± 209.0 | 900.7 ± 208.9 | 234.5 ± 24.4 (-3%) | 28.0 ± 2.8 | 1078.3 ± 22.6 (+12%) |
| Agent RL (PPO) | 924.2 ± 82.2 | 1000.0 ± 84.7 | 353.2 ± 62.2 (+46%) | 88.9 ± 27.8 | 1101.6 ± 158.3 (+14%) |
| plan_46_48_12 | 325.6 ± 39.6 | 388.7 ± 44.6 | 234.3 ± 10.2 (-3%) | 31.5 ± 4.2 | 819.9 ± 20.7 (-15%) |
| rl_ppo_romana_greu_bc | 331.9 ± 26.4 | 392.8 ± 28.9 | 253.4 ± 26.2 (+5%) | 37.9 ± 14.2 | 864.9 ± 66.6 (-10%) |
| rl_ppo_romana_greu_e7_400k | 335.1 ± 67.2 | 399.1 ± 67.5 | 227.0 ± 14.6 (-6%) | 30.1 ± 3.0 | 824.4 ± 45.4 (-14%) |
| rl_ppo_romana_zn3 | 853.6 ± 138.8 | 936.6 ± 143.2 | 339.4 ± 38.0 (+40%) | 115.7 ± 17.8 | 1015.5 ± 104.0 (+6%) |

## Scenariul `zi_2026-10-22_dimineata`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 171.6 ± 39.4 | 165.6 | 254.8 ± 42.5 | 60.6 ± 4.9 | 379.2 ± 40.4 | 13.0 ± 0.7 | 2177 ± 58 | 372 ± 93 | 2041 ± 131 |
| Plan fix (Webster) | 251.0 ± 9.1 (+46%) | 250.1 (+51%) | 350.4 ± 9.8 | 57.7 ± 6.4 | 474.3 ± 9.7 | 29.1 ± 0.6 | 2143 ± 7 | 418 ± 112 | 2410 ± 39 |
| Actuated SUMO | 133.8 ± 69.2 (-22%) | 101.7 (-39%) | 204.7 ± 70.5 | 72.3 ± 13.5 | 330.5 ± 67.2 | 15.0 ± 1.5 | 2248 ± 131 | 559 ± 288 | 1892 ± 199 |
| Max-Pressure | 283.8 ± 50.9 (+65%) | 258.7 (+56%) | 394.2 ± 48.4 | 87.1 ± 13.3 | 515.5 ± 46.4 | 23.1 ± 3.6 | 2091 ± 69 | 429 ± 130 | 2531 ± 127 |
| Agent RL (PPO) | 252.7 ± 49.0 (+47%) | 245.4 (+48%) | 352.7 ± 40.7 | 80.9 ± 17.2 | 476.3 ± 38.9 | 15.9 ± 1.6 | 2123 ± 97 | 398 ± 183 | 2380 ± 72 |
| plan_46_48_12 | 120.3 ± 16.5 (-30%) | 113.9 (-31%) | 197.6 ± 24.4 | 56.6 ± 5.7 | 324.8 ± 24.4 | 14.8 ± 1.4 | 2251 ± 32 | 463 ± 75 | 1866 ± 73 |
| rl_ppo_romana_greu_bc | 121.7 ± 32.9 (-29%) | 118.5 (-28%) | 195.3 ± 43.2 | 65.9 ± 15.6 | 321.9 ± 42.3 | 15.1 ± 1.9 | 2261 ± 50 | 338 ± 69 | 1861 ± 140 |
| rl_ppo_romana_greu_e7_400k | 131.4 ± 24.6 (-23%) | 136.9 (-17%) | 212.3 ± 28.3 | 71.3 ± 13.6 | 339.2 ± 28.0 | 15.7 ± 1.9 | 2254 ± 51 | 333 ± 137 | 1920 ± 85 |
| rl_ppo_romana_zn3 | 212.9 ± 98.6 (+24%) | 189.9 (+15%) | 301.9 ± 94.5 | 62.9 ± 21.7 | 426.8 ± 90.9 | 16.0 ± 7.6 | 2145 ± 161 | 445 ± 356 | 2208 ± 259 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 94.4 ± 10.2 | 136.1 ± 12.2 | 215.5 ± 40.9 | 24.1 ± 6.2 | 382.2 ± 49.1 |
| Plan fix (Webster) | 121.4 ± 27.8 | 169.8 ± 29.1 | 199.4 ± 24.6 (-7%) | 27.6 ± 6.7 | 428.4 ± 17.5 (+12%) |
| Actuated SUMO | 106.1 ± 66.6 | 148.1 ± 68.8 | 285.2 ± 52.1 (+32%) | 40.1 ± 13.7 | 418.4 ± 74.5 (+9%) |
| Max-Pressure | 123.7 ± 36.4 | 175.8 ± 44.7 | 169.1 ± 22.1 (-22%) | 13.1 ± 2.4 | 446.7 ± 47.5 (+17%) |
| Agent RL (PPO) | 154.5 ± 69.7 | 200.1 ± 70.3 | 181.0 ± 43.5 (-16%) | 14.3 ± 2.2 | 426.2 ± 45.3 (+12%) |
| plan_46_48_12 | 81.0 ± 6.2 | 122.5 ± 7.6 | 265.9 ± 22.0 (+23%) | 37.1 ± 8.6 | 386.6 ± 14.8 (+1%) |
| rl_ppo_romana_greu_bc | 88.3 ± 12.3 | 128.9 ± 13.1 | 233.0 ± 44.8 (+8%) | 33.3 ± 4.3 | 364.1 ± 36.3 (-5%) |
| rl_ppo_romana_greu_e7_400k | 80.7 ± 17.2 | 122.7 ± 21.4 | 234.9 ± 37.9 (+9%) | 30.9 ± 5.6 | 379.5 ± 38.1 (-1%) |
| rl_ppo_romana_zn3 | 125.3 ± 65.8 | 169.1 ± 65.8 | 189.6 ± 30.4 (-12%) | 27.8 ± 18.9 | 390.2 ± 62.7 (+2%) |

## Scenariul `zi_2026-10-22_linistit`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 46.5 ± 1.5 | 46.7 | 81.1 ± 2.1 | 0.5 ± 0.0 | 206.9 ± 2.0 | 1.2 ± 0.1 | 314 ± 0 | 0 ± 0 | 196 ± 2 |
| Plan fix (Webster) | 42.4 ± 0.9 (-9%) | 42.0 (-10%) | 77.9 ± 1.1 | 0.5 ± 0.0 | 203.6 ± 1.0 | 1.0 ± 0.0 | 314 ± 0 | 0 ± 0 | 195 ± 1 |
| Actuated SUMO | 40.8 ± 1.3 (-12%) | 40.9 (-12%) | 75.9 ± 1.5 | 0.5 ± 0.1 | 201.6 ± 1.2 | 0.8 ± 0.0 | 314 ± 0 | 0 ± 0 | 193 ± 1 |
| Max-Pressure | 37.6 ± 0.9 (-19%) | 37.4 (-20%) | 71.3 ± 1.5 | 1.3 ± 0.4 | 197.0 ± 1.4 | 0.4 ± 0.0 | 314 ± 0 | 0 ± 0 | 190 ± 1 |
| Agent RL (PPO) | 40.3 ± 1.3 (-13%) | 40.7 (-13%) | 75.7 ± 1.9 | 0.6 ± 0.1 | 201.5 ± 1.7 | 0.7 ± 0.1 | 314 ± 0 | 0 ± 0 | 195 ± 2 |
| plan_46_48_12 | 53.1 ± 1.1 (+14%) | 53.2 (+14%) | 89.0 ± 1.4 | 0.5 ± 0.0 | 214.7 ± 1.4 | 1.6 ± 0.1 | 314 ± 0 | 0 ± 0 | 200 ± 1 |
| rl_ppo_romana_greu_bc | 56.0 ± 2.2 (+21%) | 56.6 (+21%) | 91.6 ± 2.3 | 0.5 ± 0.0 | 217.3 ± 2.5 | 1.8 ± 0.1 | 314 ± 0 | 0 ± 0 | 201 ± 2 |
| rl_ppo_romana_greu_e7_400k | 56.6 ± 1.0 (+22%) | 56.9 (+22%) | 92.1 ± 1.6 | 0.5 ± 0.0 | 217.8 ± 1.3 | 1.8 ± 0.0 | 314 ± 0 | 0 ± 0 | 201 ± 2 |
| rl_ppo_romana_zn3 | 32.0 ± 1.1 (-31%) | 32.0 (-31%) | 65.7 ± 1.4 | 1.3 ± 1.0 | 191.5 ± 1.2 | 0.4 ± 0.0 | 314 ± 0 | 0 ± 0 | 188 ± 2 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 150.4 ± 8.7 | 0.1 ± 0.0 | 8.0 ± 0.2 |
| Plan fix (Webster) | nan ± nan | nan ± nan | 115.7 ± 5.9 (-23%) | 0.1 ± 0.0 | 7.5 ± 0.1 (-6%) |
| Actuated SUMO | nan ± nan | nan ± nan | 128.3 ± 3.9 (-15%) | 0.1 ± 0.0 | 7.4 ± 0.1 (-7%) |
| Max-Pressure | nan ± nan | nan ± nan | 230.9 ± 8.4 (+54%) | 0.1 ± 0.0 | 7.6 ± 0.1 (-4%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 127.4 ± 5.5 (-15%) | 0.1 ± 0.0 | 7.4 ± 0.2 (-8%) |
| plan_46_48_12 | nan ± nan | nan ± nan | 157.4 ± 10.8 (+5%) | 0.1 ± 0.0 | 8.7 ± 0.1 (+9%) |
| rl_ppo_romana_greu_bc | nan ± nan | nan ± nan | 167.8 ± 6.2 (+12%) | 0.2 ± 0.0 | 9.0 ± 0.2 (+13%) |
| rl_ppo_romana_greu_e7_400k | nan ± nan | nan ± nan | 177.2 ± 6.1 (+18%) | 0.2 ± 0.0 | 9.1 ± 0.1 (+14%) |
| rl_ppo_romana_zn3 | nan ± nan | nan ± nan | 271.7 ± 31.2 (+81%) | 0.2 ± 0.0 | 7.4 ± 0.3 (-8%) |

## Scenariul `zi_2026-10-22_linistit_x0_8`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 48.0 ± 2.1 | 47.9 | 83.0 ± 2.9 | 0.6 ± 0.1 | 209.4 ± 2.7 | 1.0 ± 0.0 | 254 ± 0 | 1 ± 0 | 162 ± 2 |
| Plan fix (Webster) | 41.4 ± 0.7 (-14%) | 41.1 (-14%) | 76.6 ± 1.1 | 0.7 ± 0.0 | 203.0 ± 1.5 | 0.8 ± 0.0 | 254 ± 0 | 1 ± 0 | 160 ± 1 |
| Actuated SUMO | 40.5 ± 0.8 (-16%) | 40.8 (-15%) | 75.5 ± 1.3 | 0.6 ± 0.1 | 201.8 ± 1.0 | 0.6 ± 0.1 | 254 ± 0 | 1 ± 0 | 159 ± 2 |
| Max-Pressure | 37.0 ± 2.6 (-23%) | 38.3 (-20%) | 70.4 ± 3.2 | 0.6 ± 0.0 | 196.7 ± 3.0 | 0.3 ± 0.0 | 254 ± 0 | 1 ± 0 | 155 ± 2 |
| Agent RL (PPO) | 39.4 ± 1.3 (-18%) | 39.8 (-17%) | 74.5 ± 1.8 | 0.6 ± 0.1 | 200.8 ± 2.0 | 0.6 ± 0.1 | 254 ± 0 | 1 ± 0 | 159 ± 1 |
| plan_46_48_12 | 52.5 ± 0.7 (+9%) | 52.4 (+9%) | 88.0 ± 0.8 | 0.5 ± 0.0 | 214.3 ± 0.7 | 1.3 ± 0.0 | 254 ± 0 | 1 ± 0 | 164 ± 1 |
| rl_ppo_romana_greu_bc | 55.9 ± 1.3 (+16%) | 56.4 (+18%) | 91.3 ± 1.9 | 0.8 ± 0.3 | 217.6 ± 2.1 | 1.5 ± 0.0 | 254 ± 0 | 1 ± 0 | 165 ± 1 |
| rl_ppo_romana_greu_e7_400k | 54.8 ± 0.9 (+14%) | 54.6 (+14%) | 90.3 ± 1.0 | 0.8 ± 0.0 | 216.6 ± 0.9 | 1.4 ± 0.1 | 254 ± 0 | 1 ± 0 | 164 ± 1 |
| rl_ppo_romana_zn3 | 31.6 ± 0.9 (-34%) | 31.4 (-34%) | 65.2 ± 1.4 | 1.0 ± 1.0 | 191.6 ± 1.7 | 0.3 ± 0.0 | 254 ± 0 | 1 ± 0 | 155 ± 1 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 156.7 ± 7.7 | 0.1 ± 0.0 | 6.8 ± 0.2 |
| Plan fix (Webster) | nan ± nan | nan ± nan | 123.0 ± 5.8 (-22%) | 0.1 ± 0.0 | 6.1 ± 0.1 (-9%) |
| Actuated SUMO | nan ± nan | nan ± nan | 132.2 ± 1.9 (-16%) | 0.1 ± 0.0 | 6.1 ± 0.1 (-10%) |
| Max-Pressure | nan ± nan | nan ± nan | 218.2 ± 11.8 (+39%) | 0.1 ± 0.0 | 6.2 ± 0.2 (-8%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 131.4 ± 4.2 (-16%) | 0.1 ± 0.0 | 6.0 ± 0.1 (-11%) |
| plan_46_48_12 | nan ± nan | nan ± nan | 172.5 ± 5.8 (+10%) | 0.2 ± 0.0 | 7.2 ± 0.0 (+6%) |
| rl_ppo_romana_greu_bc | nan ± nan | nan ± nan | 186.1 ± 2.6 (+19%) | 0.2 ± 0.0 | 7.5 ± 0.2 (+11%) |
| rl_ppo_romana_greu_e7_400k | nan ± nan | nan ± nan | 184.4 ± 7.3 (+18%) | 0.3 ± 0.0 | 7.5 ± 0.1 (+10%) |
| rl_ppo_romana_zn3 | nan ± nan | nan ± nan | 292.2 ± 24.2 (+86%) | 0.3 ± 0.1 | 6.3 ± 0.2 (-7%) |

## Scenariul `zi_2026-10-22_varf`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 161.0 ± 66.4 | 133.1 | 246.6 ± 80.6 | 58.9 ± 8.1 | 374.0 ± 78.7 | 20.0 ± 3.1 | 2479 ± 53 | 482 ± 185 | 2334 ± 307 |
| Plan fix (Webster) | 172.4 ± 72.7 (+7%) | 142.6 (+7%) | 254.4 ± 90.1 | 59.4 ± 3.4 | 380.6 ± 88.5 | 24.7 ± 2.2 | 2453 ± 82 | 478 ± 214 | 2372 ± 330 |
| Actuated SUMO | 97.7 ± 18.2 (-39%) | 95.3 (-28%) | 160.2 ± 19.0 | 54.2 ± 11.8 | 288.7 ± 18.1 | 19.3 ± 2.2 | 2527 ± 26 | 487 ± 85 | 1997 ± 78 |
| Max-Pressure | 323.8 ± 91.2 (+101%) | 290.1 (+118%) | 438.0 ± 97.0 | 27.5 ± 11.6 | 561.3 ± 94.7 | 31.5 ± 3.2 | 2210 ± 109 | 735 ± 259 | 3004 ± 338 |
| Agent RL (PPO) | 266.2 ± 45.3 (+65%) | 265.4 (+99%) | 366.8 ± 37.7 | 30.0 ± 14.8 | 492.7 ± 34.4 | 25.0 ± 2.2 | 2279 ± 118 | 657 ± 206 | 2721 ± 97 |
| plan_46_48_12 | 103.4 ± 33.0 (-36%) | 88.5 (-34%) | 169.7 ± 39.4 | 57.2 ± 15.7 | 297.9 ± 39.8 | 20.4 ± 4.6 | 2527 ± 18 | 383 ± 90 | 2045 ± 170 |
| rl_ppo_romana_greu_bc | 103.5 ± 15.2 (-36%) | 111.3 (-16%) | 165.4 ± 16.6 | 46.0 ± 10.9 | 293.4 ± 15.8 | 21.2 ± 2.2 | 2522 ± 27 | 414 ± 134 | 2021 ± 75 |
| rl_ppo_romana_greu_e7_400k | 93.9 ± 9.2 (-42%) | 94.9 (-29%) | 159.5 ± 14.4 | 52.3 ± 3.3 | 288.1 ± 14.6 | 18.0 ± 0.7 | 2536 ± 20 | 370 ± 95 | 1995 ± 56 |
| rl_ppo_romana_zn3 | 170.7 ± 72.1 (+6%) | 133.5 (+0%) | 266.9 ± 77.5 | 65.7 ± 15.5 | 395.0 ± 76.5 | 17.4 ± 4.2 | 2462 ± 111 | 457 ± 295 | 2407 ± 271 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 201.9 ± 49.8 | 21.7 ± 2.2 | 377.1 ± 94.5 |
| Plan fix (Webster) | nan ± nan | nan ± nan | 183.3 ± 35.6 (-9%) | 17.5 ± 3.3 | 368.7 ± 87.6 (-2%) |
| Actuated SUMO | nan ± nan | nan ± nan | 219.1 ± 16.1 (+9%) | 38.1 ± 7.2 | 327.2 ± 26.3 (-13%) |
| Max-Pressure | nan ± nan | nan ± nan | 165.5 ± 15.9 (-18%) | 17.3 ± 2.4 | 451.1 ± 79.5 (+20%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 177.8 ± 24.2 (-12%) | 21.5 ± 4.7 | 414.4 ± 33.4 (+10%) |
| plan_46_48_12 | nan ± nan | nan ± nan | 206.1 ± 27.5 (+2%) | 31.9 ± 4.5 | 325.8 ± 51.0 (-14%) |
| rl_ppo_romana_greu_bc | nan ± nan | nan ± nan | 200.1 ± 13.2 (-1%) | 29.4 ± 3.1 | 310.3 ± 24.8 (-18%) |
| rl_ppo_romana_greu_e7_400k | nan ± nan | nan ± nan | 198.5 ± 18.3 (-2%) | 33.4 ± 2.6 | 308.8 ± 21.6 (-18%) |
| rl_ppo_romana_zn3 | nan ± nan | nan ± nan | 174.5 ± 28.1 (-14%) | 23.1 ± 9.4 | 373.0 ± 61.8 (-1%) |

## Scenariul `zi_2026-10-22_varf_x1_2`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 265.1 ± 41.0 | 245.9 | 386.2 ± 37.4 | 72.9 ± 4.2 | 511.9 ± 35.3 | 28.0 ± 2.3 | 2791 ± 130 | 601 ± 248 | 3411 ± 122 |
| Plan fix (Webster) | 280.3 ± 123.1 (+6%) | 232.2 (-6%) | 403.0 ± 131.5 | 78.6 ± 14.7 | 527.1 ± 125.9 | 31.8 ± 7.2 | 2757 ± 261 | 677 ± 325 | 3447 ± 417 |
| Actuated SUMO | 252.3 ± 69.2 (-5%) | 226.9 (-8%) | 358.9 ± 77.5 | 68.6 ± 15.9 | 482.4 ± 75.8 | 32.3 ± 2.8 | 2771 ± 120 | 887 ± 214 | 3286 ± 335 |
| Max-Pressure | 461.9 ± 61.0 (+74%) | 462.6 (+88%) | 589.7 ± 48.0 | 80.3 ± 25.0 | 705.5 ± 43.3 | 36.9 ± 3.1 | 2315 ± 223 | 1177 ± 375 | 4046 ± 95 |
| Agent RL (PPO) | 325.8 ± 39.1 (+23%) | 314.7 (+28%) | 459.3 ± 36.6 | 51.6 ± 16.6 | 582.6 ± 34.3 | 29.9 ± 1.5 | 2658 ± 143 | 821 ± 256 | 3688 ± 143 |
| plan_46_48_12 | 196.1 ± 39.9 (-26%) | 183.2 (-26%) | 300.6 ± 43.1 | 66.4 ± 11.6 | 427.3 ± 40.9 | 27.8 ± 2.5 | 2900 ± 130 | 511 ± 215 | 3045 ± 153 |
| rl_ppo_romana_greu_bc | 220.9 ± 68.4 (-17%) | 210.1 (-15%) | 328.5 ± 78.4 | 63.8 ± 15.3 | 454.0 ± 74.3 | 29.9 ± 4.5 | 2837 ± 137 | 691 ± 210 | 3165 ± 349 |
| rl_ppo_romana_greu_e7_400k | 213.1 ± 46.5 (-20%) | 226.8 (-8%) | 319.0 ± 50.4 | 74.2 ± 2.9 | 445.4 ± 48.8 | 27.1 ± 1.9 | 2868 ± 141 | 522 ± 216 | 3125 ± 194 |
| rl_ppo_romana_zn3 | 293.5 ± 34.5 (+11%) | 289.3 (+18%) | 407.6 ± 27.2 | 52.9 ± 17.6 | 531.8 ± 26.1 | 23.3 ± 2.9 | 2659 ± 124 | 911 ± 281 | 3416 ± 67 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 182.1 ± 13.0 | 24.0 ± 5.4 | 527.2 ± 35.8 |
| Plan fix (Webster) | nan ± nan | nan ± nan | 175.3 ± 15.3 (-4%) | 18.5 ± 2.2 | 535.0 ± 107.7 (+1%) |
| Actuated SUMO | nan ± nan | nan ± nan | 225.7 ± 13.8 (+24%) | 38.8 ± 3.8 | 540.4 ± 75.1 (+2%) |
| Max-Pressure | nan ± nan | nan ± nan | 181.0 ± 19.4 (-1%) | 17.0 ± 2.4 | 669.7 ± 37.1 (+27%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 175.3 ± 7.2 (-4%) | 30.1 ± 7.2 | 556.4 ± 37.3 (+6%) |
| plan_46_48_12 | nan ± nan | nan ± nan | 193.1 ± 13.5 (+6%) | 30.4 ± 4.0 | 463.2 ± 33.8 (-12%) |
| rl_ppo_romana_greu_bc | nan ± nan | nan ± nan | 203.3 ± 9.7 (+12%) | 29.1 ± 4.0 | 491.8 ± 80.5 (-7%) |
| rl_ppo_romana_greu_e7_400k | nan ± nan | nan ± nan | 198.7 ± 6.4 (+9%) | 32.2 ± 4.4 | 489.3 ± 39.8 (-7%) |
| rl_ppo_romana_zn3 | nan ± nan | nan ± nan | 181.0 ± 12.8 (-1%) | 34.6 ± 8.1 | 519.5 ± 19.0 (-1%) |
