# Rezultate – evaluare comparativă

Medii ± abatere standard pe 5 seed-uri SUMO. Procentele sunt față de plan fix de referință. Mediana pe seed-uri este dată separat pentru așteptarea vehiculelor: aproape de saturație, rețeaua poate intra sau nu în blocaj în funcție de seed, iar câteva rulări blocate trag media în sus. Generat automat de `python -m romana.control.evaluate`.


## Scenariul `zi_2026-10-21_linistit`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 36.6 ± 1.8 | 36.4 | 70.5 ± 2.4 | 2.1 ± 0.8 | 182.8 ± 2.1 | 2.6 ± 0.2 | 692 ± 0 | 8 ± 3 | 336 ± 4 |
| Actuated SUMO | 33.7 ± 0.3 (-8%) | 33.8 (-7%) | 68.1 ± 0.2 | 1.6 ± 0.2 | 180.3 ± 0.6 | 2.1 ± 0.1 | 692 ± 0 | 7 ± 3 | 334 ± 1 |
| Max-Pressure | 32.1 ± 1.2 (-13%) | 32.4 (-11%) | 66.0 ± 1.7 | 1.5 ± 0.4 | 178.2 ± 1.4 | 1.6 ± 0.1 | 692 ± 0 | 8 ± 4 | 332 ± 3 |
| Agent RL (PPO) | 37.9 ± 0.7 (+3%) | 38.1 (+5%) | 73.3 ± 1.0 | 1.3 ± 0.2 | 185.5 ± 1.2 | 2.1 ± 0.1 | 692 ± 0 | 8 ± 3 | 341 ± 2 |
| plan_46_48_12 | 44.5 ± 0.8 (+21%) | 44.5 (+22%) | 79.2 ± 1.1 | 2.7 ± 0.5 | 191.5 ± 1.5 | 3.6 ± 0.1 | 692 ± 0 | 9 ± 3 | 346 ± 2 |
| rl_ppo_romana_lejer | 28.4 ± 1.0 (-22%) | 28.2 (-22%) | 61.5 ± 1.4 | 1.7 ± 0.6 | 173.7 ± 1.2 | 1.1 ± 0.1 | 692 ± 0 | 7 ± 3 | 326 ± 3 |
| rl_ppo_romana_zn3 | 26.7 ± 0.8 (-27%) | 26.5 (-27%) | 59.5 ± 1.5 | 2.9 ± 0.8 | 171.8 ± 1.9 | 1.0 ± 0.1 | 692 ± 0 | 10 ± 3 | 324 ± 3 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 132.7 ± 1.5 | 1.2 ± 0.1 | 23.1 ± 0.4 |
| Actuated SUMO | nan ± nan | nan ± nan | 123.0 ± 2.6 (-7%) | 0.9 ± 0.1 | 21.8 ± 0.2 (-5%) |
| Max-Pressure | nan ± nan | nan ± nan | 120.8 ± 3.1 (-9%) | 0.8 ± 0.1 | 21.3 ± 0.1 (-8%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 113.5 ± 2.7 (-14%) | 0.7 ± 0.1 | 22.1 ± 0.2 (-4%) |
| plan_46_48_12 | nan ± nan | nan ± nan | 150.0 ± 1.6 (+13%) | 1.7 ± 0.1 | 26.0 ± 0.3 (+13%) |
| rl_ppo_romana_lejer | nan ± nan | nan ± nan | 128.4 ± 0.9 (-3%) | 1.0 ± 0.1 | 20.9 ± 0.2 (-9%) |
| rl_ppo_romana_zn3 | nan ± nan | nan ± nan | 144.5 ± 1.6 (+9%) | 1.5 ± 0.1 | 21.9 ± 0.4 (-5%) |

## Scenariul `zi_2026-10-21_linistit_x0_8`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 37.6 ± 1.1 | 36.9 | 70.3 ± 1.8 | 1.6 ± 0.3 | 182.2 ± 1.8 | 2.1 ± 0.1 | 555 ± 0 | 10 ± 1 | 268 ± 3 |
| Actuated SUMO | 33.2 ± 1.0 (-12%) | 33.3 (-10%) | 65.8 ± 0.9 | 1.2 ± 0.2 | 177.7 ± 1.6 | 1.5 ± 0.1 | 555 ± 0 | 10 ± 1 | 264 ± 2 |
| Max-Pressure | 31.9 ± 0.8 (-15%) | 31.8 (-14%) | 64.8 ± 1.4 | 1.4 ± 0.6 | 176.6 ± 0.9 | 1.2 ± 0.1 | 555 ± 0 | 10 ± 1 | 263 ± 2 |
| Agent RL (PPO) | 36.7 ± 0.7 (-2%) | 36.9 (+0%) | 71.1 ± 0.9 | 1.0 ± 0.2 | 183.0 ± 1.6 | 1.4 ± 0.1 | 555 ± 0 | 10 ± 1 | 271 ± 1 |
| plan_46_48_12 | 44.7 ± 1.4 (+19%) | 44.4 (+20%) | 77.6 ± 1.5 | 2.0 ± 0.4 | 189.5 ± 1.9 | 3.0 ± 0.1 | 555 ± 0 | 11 ± 1 | 273 ± 2 |
| rl_ppo_romana_lejer | 28.8 ± 0.6 (-23%) | 28.7 (-22%) | 60.1 ± 0.9 | 1.4 ± 0.3 | 171.9 ± 1.0 | 0.8 ± 0.0 | 555 ± 0 | 10 ± 1 | 257 ± 1 |
| rl_ppo_romana_zn3 | 27.5 ± 0.5 (-27%) | 27.3 (-26%) | 59.3 ± 0.4 | 2.2 ± 0.6 | 171.1 ± 0.5 | 0.8 ± 0.1 | 555 ± 0 | 11 ± 1 | 258 ± 1 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 138.6 ± 2.1 | 1.3 ± 0.0 | 20.6 ± 0.4 |
| Actuated SUMO | nan ± nan | nan ± nan | 126.3 ± 1.9 (-9%) | 0.9 ± 0.1 | 19.0 ± 0.2 (-8%) |
| Max-Pressure | nan ± nan | nan ± nan | 126.0 ± 2.9 (-9%) | 0.7 ± 0.1 | 18.8 ± 0.1 (-9%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 119.2 ± 2.4 (-14%) | 0.8 ± 0.1 | 19.3 ± 0.2 (-6%) |
| plan_46_48_12 | nan ± nan | nan ± nan | 156.1 ± 3.5 (+13%) | 1.9 ± 0.2 | 23.0 ± 0.4 (+12%) |
| rl_ppo_romana_lejer | nan ± nan | nan ± nan | 131.2 ± 0.9 (-5%) | 0.9 ± 0.1 | 18.5 ± 0.2 (-10%) |
| rl_ppo_romana_zn3 | nan ± nan | nan ± nan | 151.9 ± 4.7 (+10%) | 1.5 ± 0.1 | 19.9 ± 0.5 (-3%) |

## Scenariul `zi_2026-10-21_pranz`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 105.1 ± 28.9 | 104.8 | 164.6 ± 35.1 | 127.5 ± 14.0 | 277.2 ± 35.2 | 11.0 ± 2.3 | 1206 ± 12 | 344 ± 130 | 875 ± 76 |
| Actuated SUMO | 58.1 ± 10.8 (-45%) | 51.2 (-51%) | 101.3 ± 13.5 | 146.0 ± 31.7 | 213.0 ± 13.9 | 6.4 ± 0.9 | 1231 ± 26 | 374 ± 141 | 754 ± 27 |
| Max-Pressure | 432.6 ± 116.0 (+312%) | 490.5 (+368%) | 510.1 ± 121.9 | 77.1 ± 15.4 | 615.4 ± 120.2 | 31.3 ± 6.3 | 1015 ± 83 | 637 ± 192 | 1490 ± 208 |
| Agent RL (PPO) | 124.0 ± 7.7 (+18%) | 120.7 (+15%) | 191.9 ± 9.4 | 126.3 ± 15.6 | 305.4 ± 9.8 | 13.0 ± 0.5 | 1187 ± 13 | 277 ± 78 | 923 ± 14 |
| plan_46_48_12 | 99.8 ± 39.4 (-5%) | 89.7 (-14%) | 149.5 ± 42.9 | 138.7 ± 10.8 | 260.3 ± 43.4 | 11.2 ± 3.2 | 1217 ± 32 | 459 ± 72 | 848 ± 80 |
| rl_ppo_romana_lejer | 143.9 ± 56.8 (+37%) | 121.1 (+15%) | 204.4 ± 57.4 | 123.2 ± 39.1 | 316.1 ± 55.4 | 14.2 ± 5.0 | 1178 ± 61 | 348 ± 190 | 945 ± 86 |
| rl_ppo_romana_zn3 | 110.4 ± 44.1 (+5%) | 112.7 (+7%) | 165.2 ± 51.6 | 110.6 ± 20.6 | 278.8 ± 52.9 | 8.7 ± 1.5 | 1184 ± 29 | 423 ± 205 | 866 ± 87 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 93.2 ± 27.4 | 139.7 ± 33.1 | 200.1 ± 11.9 | 26.4 ± 7.1 | 274.9 ± 12.8 |
| Actuated SUMO | 59.5 ± 10.5 | 95.8 ± 11.8 | 214.7 ± 48.0 (+7%) | 27.4 ± 5.1 | 274.1 ± 38.3 (-0%) |
| Max-Pressure | 395.8 ± 177.4 | 461.6 ± 182.1 | 180.1 ± 35.9 (-10%) | 18.0 ± 3.1 | 350.8 ± 62.2 (+28%) |
| Agent RL (PPO) | 91.2 ± 10.6 | 141.0 ± 15.5 | 139.3 ± 5.4 (-30%) | 12.2 ± 2.0 | 229.0 ± 3.9 (-17%) |
| plan_46_48_12 | 109.7 ± 70.8 | 152.7 ± 75.5 | 210.7 ± 37.3 (+5%) | 33.5 ± 5.1 | 285.0 ± 29.7 (+4%) |
| rl_ppo_romana_lejer | 111.6 ± 29.3 | 166.2 ± 35.5 | 143.3 ± 9.6 (-28%) | 13.6 ± 3.1 | 236.6 ± 7.0 (-14%) |
| rl_ppo_romana_zn3 | 70.0 ± 12.0 | 116.2 ± 9.4 | 200.1 ± 55.5 (-0%) | 15.6 ± 2.7 | 267.6 ± 58.4 (-3%) |

## Scenariul `zi_2026-10-21_varf`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 217.8 ± 44.2 | 222.1 | 278.2 ± 46.4 | 44.3 ± 15.4 | 391.6 ± 45.1 | 23.8 ± 2.1 | 1623 ± 62 | 438 ± 169 | 1490 ± 119 |
| Actuated SUMO | 189.5 ± 32.9 (-13%) | 200.7 (-10%) | 245.7 ± 32.8 | 35.4 ± 8.2 | 360.3 ± 30.6 | 21.5 ± 2.9 | 1645 ± 63 | 740 ± 110 | 1404 ± 78 |
| Max-Pressure | 539.7 ± 145.6 (+148%) | 514.3 (+132%) | 629.9 ± 151.6 | 68.0 ± 58.1 | 736.3 ± 147.3 | 39.1 ± 5.1 | 1321 ± 158 | 928 ± 332 | 2262 ± 281 |
| Agent RL (PPO) | 393.3 ± 130.0 (+81%) | 377.0 (+70%) | 475.6 ± 133.4 | 44.5 ± 11.2 | 587.0 ± 128.6 | 32.5 ± 4.2 | 1421 ± 130 | 1210 ± 200 | 1908 ± 287 |
| plan_46_48_12 | 225.7 ± 46.9 (+4%) | 252.8 (+14%) | 284.3 ± 47.0 | 37.6 ± 7.8 | 397.7 ± 44.3 | 24.6 ± 3.0 | 1619 ± 66 | 694 ± 181 | 1506 ± 109 |
| rl_ppo_romana_lejer | 321.7 ± 113.8 (+48%) | 346.9 (+56%) | 400.5 ± 115.9 | 42.7 ± 19.5 | 513.8 ± 110.8 | 28.6 ± 5.5 | 1503 ± 164 | 744 ± 384 | 1744 ± 233 |
| rl_ppo_romana_zn3 | 224.5 ± 69.5 (+3%) | 202.6 (-9%) | 293.9 ± 71.6 | 24.6 ± 10.6 | 410.2 ± 69.2 | 25.1 ± 3.9 | 1592 ± 107 | 844 ± 172 | 1505 ± 148 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 240.6 ± 50.4 | 300.5 ± 45.5 | 178.7 ± 9.6 | 24.1 ± 4.2 | 316.7 ± 34.4 |
| Actuated SUMO | 186.2 ± 45.6 | 245.6 ± 47.5 | 232.4 ± 29.1 (+30%) | 38.8 ± 6.1 | 344.4 ± 38.9 (+9%) |
| Max-Pressure | 818.4 ± 209.0 | 913.3 ± 205.6 | 196.7 ± 29.0 (+10%) | 19.5 ± 2.5 | 493.5 ± 104.9 (+56%) |
| Agent RL (PPO) | 510.8 ± 315.7 | 585.6 ± 322.2 | 207.5 ± 36.6 (+16%) | 50.7 ± 20.4 | 425.4 ± 81.1 (+34%) |
| plan_46_48_12 | 251.7 ± 68.1 | 309.0 ± 67.5 | 219.6 ± 20.6 (+23%) | 30.7 ± 5.6 | 353.0 ± 17.9 (+11%) |
| rl_ppo_romana_lejer | 422.8 ± 157.6 | 490.1 ± 162.2 | 194.8 ± 33.3 (+9%) | 22.7 ± 4.8 | 381.0 ± 72.5 (+20%) |
| rl_ppo_romana_zn3 | 393.8 ± 279.6 | 468.7 ± 302.9 | 196.8 ± 23.1 (+10%) | 49.6 ± 16.4 | 326.5 ± 41.1 (+3%) |

## Scenariul `zi_2026-10-21_varf_x1_2`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 334.8 ± 54.3 | 318.5 | 411.9 ± 50.9 | 81.8 ± 41.8 | 522.1 ± 49.0 | 29.7 ± 3.7 | 1855 ± 103 | 759 ± 231 | 2204 ± 76 |
| Actuated SUMO | 342.0 ± 54.9 (+2%) | 371.9 (+17%) | 407.7 ± 54.4 | 83.4 ± 23.8 | 515.6 ± 53.8 | 31.0 ± 2.4 | 1763 ± 64 | 1007 ± 141 | 2131 ± 114 |
| Max-Pressure | 646.3 ± 92.1 (+93%) | 631.7 (+98%) | 752.2 ± 91.8 | 109.2 ± 30.6 | 857.9 ± 91.1 | 41.9 ± 3.3 | 1457 ± 107 | 1194 ± 249 | 2949 ± 177 |
| Agent RL (PPO) | 574.2 ± 90.9 (+71%) | 596.4 (+87%) | 666.4 ± 81.0 | 67.4 ± 12.3 | 772.9 ± 78.7 | 39.1 ± 3.1 | 1461 ± 156 | 1557 ± 256 | 2685 ± 149 |
| plan_46_48_12 | 340.2 ± 33.1 (+2%) | 343.8 (+8%) | 410.7 ± 34.2 | 63.7 ± 14.6 | 518.9 ± 33.2 | 31.8 ± 1.4 | 1790 ± 43 | 895 ± 171 | 2168 ± 79 |
| rl_ppo_romana_lejer | 513.1 ± 107.3 (+53%) | 543.4 (+71%) | 614.3 ± 101.8 | 70.6 ± 20.4 | 723.8 ± 95.7 | 34.6 ± 4.6 | 1602 ± 161 | 999 ± 407 | 2678 ± 229 |
| rl_ppo_romana_zn3 | 458.1 ± 209.1 (+37%) | 388.3 (+22%) | 548.2 ± 204.4 | 36.8 ± 10.6 | 658.9 ± 201.4 | 34.8 ± 6.5 | 1599 ± 236 | 1398 ± 492 | 2402 ± 345 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 413.2 ± 122.2 | 491.1 ± 124.9 | 203.3 ± 11.7 | 26.3 ± 5.3 | 466.4 ± 48.3 |
| Actuated SUMO | 418.4 ± 93.1 | 478.1 ± 96.0 | 250.2 ± 17.8 (+23%) | 40.3 ± 3.4 | 502.4 ± 51.3 (+8%) |
| Max-Pressure | 889.2 ± 248.0 | 984.7 ± 248.3 | 204.0 ± 23.4 (+0%) | 18.9 ± 1.8 | 633.5 ± 49.3 (+36%) |
| Agent RL (PPO) | 836.8 ± 194.8 | 913.2 ± 195.2 | 251.3 ± 25.7 (+24%) | 63.1 ± 6.2 | 607.7 ± 47.7 (+30%) |
| plan_46_48_12 | 427.1 ± 138.2 | 488.7 ± 140.7 | 233.4 ± 23.1 (+15%) | 35.6 ± 5.7 | 480.8 ± 42.4 (+3%) |
| rl_ppo_romana_lejer | 745.3 ± 200.1 | 841.4 ± 220.0 | 207.9 ± 18.9 (+2%) | 29.1 ± 6.9 | 557.3 ± 73.2 (+19%) |
| rl_ppo_romana_zn3 | 786.3 ± 255.8 | 869.8 ± 252.3 | 250.9 ± 40.7 (+23%) | 74.8 ± 26.3 | 531.1 ± 118.6 (+14%) |

## Scenariul `zi_2026-10-22_dimineata`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 323.2 ± 83.1 | 293.2 | 397.8 ± 87.7 | 100.5 ± 38.5 | 507.9 ± 86.1 | 27.1 ± 2.5 | 1449 ± 55 | 560 ± 138 | 1708 ± 205 |
| Actuated SUMO | 162.0 ± 81.6 (-50%) | 115.2 (-61%) | 221.5 ± 83.1 | 92.6 ± 22.5 | 335.6 ± 80.7 | 18.7 ± 5.5 | 1609 ± 72 | 512 ± 146 | 1317 ± 195 |
| Max-Pressure | 701.1 ± 200.7 (+117%) | 745.2 (+154%) | 790.4 ± 194.1 | 75.1 ± 23.9 | 890.5 ± 188.2 | 40.7 ± 6.2 | 1082 ± 187 | 962 ± 245 | 2415 ± 296 |
| Agent RL (PPO) | 318.7 ± 84.2 (-1%) | 318.3 (+9%) | 401.2 ± 84.1 | 58.5 ± 22.5 | 513.9 ± 79.8 | 26.3 ± 6.1 | 1377 ± 118 | 695 ± 237 | 1654 ± 157 |
| plan_46_48_12 | 252.4 ± 91.0 (-22%) | 258.5 (-12%) | 315.9 ± 90.7 | 93.3 ± 22.4 | 426.1 ± 85.9 | 25.0 ± 5.1 | 1528 ± 92 | 471 ± 240 | 1545 ± 209 |
| rl_ppo_romana_lejer | 366.5 ± 188.0 (+13%) | 351.6 (+20%) | 450.1 ± 185.0 | 71.4 ± 46.8 | 561.9 ± 180.2 | 28.9 ± 9.7 | 1356 ± 212 | 615 ± 377 | 1757 ± 337 |
| rl_ppo_romana_zn3 | 346.1 ± 174.7 (+7%) | 281.6 (-4%) | 429.7 ± 166.4 | 52.9 ± 18.4 | 541.0 ± 160.0 | 21.8 ± 8.4 | 1362 ± 182 | 884 ± 433 | 1702 ± 311 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 95.0 ± 22.0 | 140.3 ± 28.7 | 219.8 ± 47.1 | 25.0 ± 5.2 | 407.1 ± 62.4 |
| Actuated SUMO | 64.4 ± 17.7 | 102.6 ± 17.8 | 287.2 ± 63.5 (+31%) | 39.5 ± 11.0 | 385.8 ± 46.9 (-5%) |
| Max-Pressure | 405.6 ± 376.3 | 476.7 ± 402.7 | 198.5 ± 19.2 (-10%) | 20.8 ± 3.9 | 519.4 ± 85.8 (+28%) |
| Agent RL (PPO) | 237.6 ± 76.8 | 296.2 ± 80.6 | 211.3 ± 31.7 (-4%) | 28.4 ± 13.9 | 372.7 ± 48.4 (-8%) |
| plan_46_48_12 | 117.8 ± 53.1 | 159.0 ± 54.8 | 224.4 ± 20.2 (+2%) | 33.9 ± 4.5 | 376.5 ± 47.0 (-8%) |
| rl_ppo_romana_lejer | 216.2 ± 95.3 | 270.6 ± 92.7 | 186.7 ± 35.3 (-15%) | 25.7 ± 10.4 | 377.7 ± 79.2 (-7%) |
| rl_ppo_romana_zn3 | 228.4 ± 44.6 | 278.3 ± 40.5 | 248.8 ± 41.7 (+13%) | 39.7 ± 25.3 | 415.1 ± 87.3 (+2%) |

## Scenariul `zi_2026-10-22_linistit`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 41.2 ± 1.6 | 41.1 | 72.4 ± 1.6 | 0.5 ± 0.0 | 191.8 ± 1.7 | 0.6 ± 0.0 | 169 ± 0 | 1 ± 0 | 97 ± 0 |
| Actuated SUMO | 35.9 ± 0.7 (-13%) | 36.3 (-12%) | 68.3 ± 1.1 | 0.5 ± 0.1 | 187.7 ± 1.4 | 0.4 ± 0.0 | 169 ± 0 | 1 ± 0 | 97 ± 0 |
| Max-Pressure | 34.8 ± 1.1 (-15%) | 34.8 (-15%) | 65.9 ± 1.2 | 0.9 ± 0.7 | 185.3 ± 1.4 | 0.2 ± 0.0 | 169 ± 0 | 1 ± 0 | 96 ± 1 |
| Agent RL (PPO) | 32.4 ± 0.8 (-21%) | 32.1 (-22%) | 64.3 ± 1.4 | 0.5 ± 0.0 | 183.7 ± 1.7 | 0.3 ± 0.0 | 169 ± 0 | 1 ± 0 | 96 ± 1 |
| plan_46_48_12 | 43.5 ± 1.3 (+6%) | 43.4 (+6%) | 74.9 ± 1.6 | 0.5 ± 0.0 | 194.3 ± 2.0 | 0.7 ± 0.0 | 169 ± 0 | 1 ± 0 | 98 ± 1 |
| rl_ppo_romana_lejer | 32.0 ± 1.3 (-22%) | 31.4 (-24%) | 61.9 ± 1.6 | 1.3 ± 0.8 | 181.2 ± 1.6 | 0.1 ± 0.0 | 169 ± 0 | 1 ± 0 | 94 ± 1 |
| rl_ppo_romana_zn3 | 28.1 ± 0.9 (-32%) | 27.8 (-32%) | 59.0 ± 1.2 | 0.5 ± 0.0 | 178.4 ± 1.6 | 0.2 ± 0.0 | 169 ± 0 | 1 ± 1 | 94 ± 1 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 118.1 ± 4.8 | 0.1 ± 0.0 | 4.1 ± 0.1 |
| Actuated SUMO | nan ± nan | nan ± nan | 102.9 ± 3.0 (-13%) | 0.0 ± 0.0 | 3.8 ± 0.1 (-7%) |
| Max-Pressure | nan ± nan | nan ± nan | 168.6 ± 19.1 (+43%) | 0.1 ± 0.0 | 4.1 ± 0.1 (-0%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 110.8 ± 4.2 (-6%) | 0.1 ± 0.0 | 3.7 ± 0.1 (-10%) |
| plan_46_48_12 | nan ± nan | nan ± nan | 137.6 ± 6.1 (+16%) | 0.1 ± 0.0 | 4.3 ± 0.1 (+5%) |
| rl_ppo_romana_lejer | nan ± nan | nan ± nan | 189.4 ± 18.6 (+60%) | 0.1 ± 0.0 | 4.0 ± 0.2 (-1%) |
| rl_ppo_romana_zn3 | nan ± nan | nan ± nan | 192.8 ± 27.2 (+63%) | 0.2 ± 0.1 | 3.9 ± 0.2 (-5%) |

## Scenariul `zi_2026-10-22_linistit_x0_8`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 40.6 ± 1.7 | 40.7 | 71.6 ± 2.0 | 0.5 ± 0.0 | 191.3 ± 2.4 | 0.5 ± 0.0 | 136 ± 0 | 1 ± 1 | 81 ± 1 |
| Actuated SUMO | 36.3 ± 1.6 (-10%) | 37.2 (-9%) | 69.0 ± 2.2 | 0.5 ± 0.1 | 188.7 ± 1.5 | 0.3 ± 0.0 | 136 ± 0 | 0 ± 0 | 81 ± 1 |
| Max-Pressure | 34.2 ± 2.1 (-16%) | 34.8 (-15%) | 64.4 ± 2.3 | 1.1 ± 0.4 | 184.0 ± 2.2 | 0.1 ± 0.0 | 136 ± 0 | 1 ± 1 | 79 ± 1 |
| Agent RL (PPO) | 33.3 ± 0.9 (-18%) | 33.2 (-18%) | 64.8 ± 1.5 | 0.5 ± 0.0 | 184.5 ± 2.0 | 0.3 ± 0.0 | 136 ± 0 | 1 ± 1 | 80 ± 1 |
| plan_46_48_12 | 45.9 ± 0.6 (+13%) | 46.1 (+13%) | 77.4 ± 0.8 | 0.5 ± 0.0 | 197.1 ± 1.4 | 0.6 ± 0.0 | 136 ± 0 | 0 ± 0 | 83 ± 0 |
| rl_ppo_romana_lejer | 31.0 ± 1.6 (-23%) | 31.6 (-22%) | 60.8 ± 1.7 | 1.5 ± 0.3 | 180.5 ± 2.5 | 0.1 ± 0.0 | 136 ± 0 | 1 ± 0 | 78 ± 0 |
| rl_ppo_romana_zn3 | 30.8 ± 1.2 (-24%) | 31.1 (-24%) | 62.3 ± 1.3 | 0.5 ± 0.0 | 182.0 ± 2.0 | 0.2 ± 0.0 | 136 ± 0 | 1 ± 1 | 80 ± 0 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 160.3 ± 5.1 | 0.1 ± 0.0 | 3.6 ± 0.1 |
| Actuated SUMO | nan ± nan | nan ± nan | 134.6 ± 8.7 (-16%) | 0.0 ± 0.0 | 3.4 ± 0.1 (-7%) |
| Max-Pressure | nan ± nan | nan ± nan | 314.0 ± 33.9 (+96%) | 0.1 ± 0.0 | 4.2 ± 0.2 (+17%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 158.2 ± 10.2 (-1%) | 0.1 ± 0.0 | 3.3 ± 0.0 (-7%) |
| plan_46_48_12 | nan ± nan | nan ± nan | 184.9 ± 3.8 (+15%) | 0.1 ± 0.0 | 4.0 ± 0.0 (+10%) |
| rl_ppo_romana_lejer | nan ± nan | nan ± nan | 314.5 ± 5.4 (+96%) | 0.1 ± 0.0 | 4.1 ± 0.1 (+13%) |
| rl_ppo_romana_zn3 | nan ± nan | nan ± nan | 241.6 ± 10.9 (+51%) | 0.2 ± 0.0 | 3.7 ± 0.1 (+3%) |

## Scenariul `zi_2026-10-22_varf`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 228.3 ± 63.0 | 222.2 | 292.9 ± 66.1 | 50.7 ± 5.4 | 405.9 ± 63.5 | 22.3 ± 2.7 | 1610 ± 63 | 484 ± 106 | 1636 ± 183 |
| Actuated SUMO | 216.1 ± 112.6 (-5%) | 170.9 (-23%) | 276.2 ± 120.8 | 68.8 ± 41.5 | 389.8 ± 116.4 | 21.3 ± 5.0 | 1610 ± 84 | 684 ± 305 | 1584 ± 323 |
| Max-Pressure | 454.7 ± 87.4 (+99%) | 443.5 (+100%) | 532.6 ± 92.2 | 50.8 ± 16.6 | 639.1 ± 91.2 | 36.4 ± 3.9 | 1330 ± 80 | 838 ± 177 | 2160 ± 202 |
| Agent RL (PPO) | 335.3 ± 168.7 (+47%) | 296.2 (+33%) | 419.5 ± 174.0 | 45.0 ± 12.1 | 534.4 ± 168.6 | 30.5 ± 9.0 | 1470 ± 173 | 823 ± 406 | 1879 ± 375 |
| plan_46_48_12 | 231.2 ± 56.6 (+1%) | 252.5 (+14%) | 288.2 ± 55.5 | 59.1 ± 13.5 | 398.9 ± 51.6 | 23.4 ± 3.1 | 1562 ± 93 | 631 ± 136 | 1598 ± 124 |
| rl_ppo_romana_lejer | 309.1 ± 68.7 (+35%) | 332.5 (+50%) | 382.5 ± 64.6 | 35.1 ± 24.0 | 498.0 ± 61.1 | 29.0 ± 4.6 | 1426 ± 105 | 885 ± 255 | 1758 ± 129 |
| rl_ppo_romana_zn3 | 231.6 ± 129.7 (+1%) | 146.7 (-34%) | 299.6 ± 140.1 | 42.6 ± 19.5 | 415.3 ± 139.0 | 22.8 ± 5.4 | 1551 ± 146 | 811 ± 317 | 1594 ± 302 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 185.7 ± 11.2 | 24.4 ± 2.8 | 315.6 ± 38.6 |
| Actuated SUMO | nan ± nan | nan ± nan | 233.6 ± 41.8 (+26%) | 35.7 ± 2.9 | 354.2 ± 111.6 (+12%) |
| Max-Pressure | nan ± nan | nan ± nan | 173.2 ± 19.2 (-7%) | 17.8 ± 1.7 | 407.4 ± 53.3 (+29%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 187.7 ± 21.9 (+1%) | 35.1 ± 18.3 | 361.1 ± 87.8 (+14%) |
| plan_46_48_12 | nan ± nan | nan ± nan | 213.4 ± 16.1 (+15%) | 33.8 ± 2.2 | 339.1 ± 22.6 (+7%) |
| rl_ppo_romana_lejer | nan ± nan | nan ± nan | 170.8 ± 14.4 (-8%) | 25.1 ± 8.7 | 324.0 ± 27.0 (+3%) |
| rl_ppo_romana_zn3 | nan ± nan | nan ± nan | 188.9 ± 42.0 (+2%) | 41.4 ± 13.8 | 309.8 ± 85.4 (-2%) |

## Scenariul `zi_2026-10-22_varf_x1_2`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 362.8 ± 75.3 | 342.9 | 437.4 ± 76.7 | 87.2 ± 24.2 | 545.8 ± 75.4 | 30.8 ± 4.6 | 1753 ± 116 | 708 ± 257 | 2329 ± 147 |
| Actuated SUMO | 326.6 ± 64.5 (-10%) | 351.6 (+3%) | 394.7 ± 68.0 | 94.8 ± 36.9 | 502.9 ± 65.4 | 30.7 ± 2.6 | 1768 ± 85 | 883 ± 126 | 2199 ± 173 |
| Max-Pressure | 732.2 ± 202.4 (+102%) | 776.6 (+126%) | 823.5 ± 204.1 | 75.3 ± 21.0 | 928.0 ± 201.9 | 48.0 ± 9.2 | 1275 ± 184 | 1319 ± 232 | 3032 ± 397 |
| Agent RL (PPO) | 419.6 ± 77.0 (+16%) | 430.2 (+25%) | 518.8 ± 73.6 | 55.2 ± 14.8 | 631.6 ± 68.9 | 34.1 ± 3.4 | 1632 ± 151 | 1105 ± 273 | 2473 ± 147 |
| plan_46_48_12 | 338.0 ± 30.4 (-7%) | 328.9 (-4%) | 407.3 ± 27.1 | 88.4 ± 11.8 | 514.7 ± 25.7 | 30.1 ± 2.5 | 1767 ± 62 | 765 ± 91 | 2263 ± 39 |
| rl_ppo_romana_lejer | 459.7 ± 49.7 (+27%) | 442.8 (+29%) | 556.0 ± 48.6 | 32.7 ± 16.8 | 666.4 ± 45.6 | 38.2 ± 1.7 | 1516 ± 74 | 1136 ± 156 | 2520 ± 101 |
| rl_ppo_romana_zn3 | 423.0 ± 42.5 (+17%) | 434.0 (+27%) | 515.5 ± 42.8 | 38.4 ± 9.4 | 627.0 ± 41.4 | 36.3 ± 2.9 | 1562 ± 84 | 1449 ± 179 | 2419 ± 94 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 200.9 ± 16.8 | 23.6 ± 6.5 | 453.8 ± 55.3 |
| Actuated SUMO | nan ± nan | nan ± nan | 238.6 ± 2.6 (+19%) | 42.4 ± 9.0 | 467.8 ± 51.5 (+3%) |
| Max-Pressure | nan ± nan | nan ± nan | 214.3 ± 19.2 (+7%) | 23.0 ± 4.2 | 604.9 ± 88.6 (+33%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 213.6 ± 16.3 (+6%) | 44.3 ± 12.7 | 474.5 ± 45.7 (+5%) |
| plan_46_48_12 | nan ± nan | nan ± nan | 216.0 ± 14.1 (+8%) | 35.7 ± 11.8 | 455.2 ± 21.3 (+0%) |
| rl_ppo_romana_lejer | nan ± nan | nan ± nan | 194.5 ± 10.2 (-3%) | 38.3 ± 3.6 | 462.0 ± 36.8 (+2%) |
| rl_ppo_romana_zn3 | nan ± nan | nan ± nan | 232.9 ± 21.9 (+16%) | 77.5 ± 10.3 | 476.3 ± 26.8 (+5%) |

## Scenariul `zi_2026-10-25_dimineata`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 44.8 ± 3.0 | 44.1 | 83.7 ± 3.0 | 0.8 ± 0.1 | 206.7 ± 2.9 | 2.9 ± 0.4 | 790 ± 0 | 20 ± 2 | 528 ± 4 |
| Actuated SUMO | 40.1 ± 1.4 (-11%) | 39.3 (-11%) | 78.6 ± 2.4 | 0.7 ± 0.1 | 201.7 ± 2.0 | 2.2 ± 0.2 | 790 ± 0 | 17 ± 2 | 522 ± 5 |
| Agent RL (PPO) | 45.5 ± 2.0 (+1%) | 44.7 (+1%) | 86.7 ± 2.2 | 0.7 ± 0.1 | 209.7 ± 2.1 | 2.6 ± 0.3 | 790 ± 0 | 18 ± 3 | 541 ± 5 |
| rl_ppo_romana_lejer | 40.2 ± 4.6 (-10%) | 38.7 (-12%) | 79.3 ± 5.3 | 0.7 ± 0.0 | 202.4 ± 5.1 | 1.7 ± 0.5 | 790 ± 0 | 19 ± 2 | 527 ± 7 |
| rl_ppo_romana_zn3 | 36.6 ± 1.1 (-18%) | 36.8 (-17%) | 75.3 ± 1.4 | 0.9 ± 0.2 | 198.4 ± 1.2 | 1.5 ± 0.1 | 790 ± 0 | 20 ± 3 | 523 ± 3 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 45.9 ± 3.7 | 82.3 ± 4.2 | 141.9 ± 3.0 | 2.7 ± 0.3 | 36.3 ± 0.6 |
| Actuated SUMO | 37.3 ± 10.1 | 71.8 ± 13.0 | 133.3 ± 2.2 (-6%) | 2.1 ± 0.1 | 34.1 ± 0.5 (-6%) |
| Agent RL (PPO) | 43.7 ± 13.8 | 79.4 ± 17.8 | 119.6 ± 1.4 (-16%) | 1.5 ± 0.1 | 34.2 ± 0.6 (-6%) |
| rl_ppo_romana_lejer | 43.0 ± 20.6 | 81.0 ± 24.9 | 127.5 ± 4.3 (-10%) | 1.8 ± 0.2 | 33.5 ± 1.7 (-8%) |
| rl_ppo_romana_zn3 | 35.6 ± 15.2 | 70.8 ± 16.7 | 136.5 ± 2.7 (-4%) | 2.4 ± 0.1 | 33.8 ± 0.3 (-7%) |

## Scenariul `zi_2026-10-25_linistit`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 40.1 ± 1.1 | 39.9 | 75.2 ± 1.5 | 0.5 ± 0.0 | 191.4 ± 1.3 | 1.5 ± 0.1 | 401 ± 0 | 5 ± 3 | 261 ± 2 |
| Actuated SUMO | 34.1 ± 1.7 (-15%) | 33.9 (-15%) | 68.9 ± 2.9 | 0.5 ± 0.0 | 185.2 ± 3.4 | 1.0 ± 0.1 | 401 ± 0 | 5 ± 3 | 256 ± 5 |
| Agent RL (PPO) | 42.5 ± 0.8 (+6%) | 42.5 (+7%) | 81.1 ± 1.2 | 0.5 ± 0.0 | 197.3 ± 1.7 | 1.3 ± 0.1 | 401 ± 0 | 6 ± 3 | 270 ± 2 |
| rl_ppo_romana_lejer | 30.7 ± 1.4 (-24%) | 30.6 (-23%) | 64.2 ± 2.5 | 0.5 ± 0.0 | 180.4 ± 2.5 | 0.4 ± 0.0 | 401 ± 0 | 6 ± 3 | 252 ± 3 |
| rl_ppo_romana_zn3 | 28.6 ± 0.7 (-29%) | 28.4 (-29%) | 62.9 ± 1.3 | 0.5 ± 0.0 | 179.2 ± 1.3 | 0.5 ± 0.1 | 401 ± 0 | 6 ± 3 | 252 ± 2 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 128.1 ± 2.1 | 0.8 ± 0.0 | 14.9 ± 0.2 |
| Actuated SUMO | nan ± nan | nan ± nan | 117.1 ± 3.4 (-9%) | 0.5 ± 0.1 | 13.7 ± 0.4 (-8%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 111.4 ± 2.8 (-13%) | 0.5 ± 0.0 | 14.8 ± 0.2 (-1%) |
| rl_ppo_romana_lejer | nan ± nan | nan ± nan | 138.7 ± 9.2 (+8%) | 0.7 ± 0.1 | 14.3 ± 0.5 (-5%) |
| rl_ppo_romana_zn3 | nan ± nan | nan ± nan | 141.9 ± 5.4 (+11%) | 0.9 ± 0.1 | 14.3 ± 0.2 (-4%) |

## Scenariul `zi_2026-10-25_linistit_x0_8`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 37.8 ± 1.7 | 38.5 | 71.4 ± 2.8 | 0.5 ± 0.0 | 187.7 ± 2.7 | 1.1 ± 0.1 | 324 ± 0 | 7 ± 1 | 207 ± 3 |
| Actuated SUMO | 34.1 ± 1.1 (-10%) | 34.0 (-12%) | 68.4 ± 2.1 | 0.6 ± 0.0 | 184.6 ± 2.5 | 0.8 ± 0.0 | 324 ± 0 | 6 ± 1 | 207 ± 3 |
| Agent RL (PPO) | 39.6 ± 2.0 (+5%) | 39.3 (+2%) | 76.0 ± 2.0 | 0.5 ± 0.0 | 192.3 ± 2.1 | 0.8 ± 0.1 | 324 ± 0 | 7 ± 1 | 213 ± 1 |
| rl_ppo_romana_lejer | 29.8 ± 0.9 (-21%) | 30.0 (-22%) | 62.7 ± 1.3 | 0.5 ± 0.0 | 179.0 ± 1.6 | 0.4 ± 0.0 | 324 ± 0 | 8 ± 2 | 203 ± 2 |
| rl_ppo_romana_zn3 | 29.4 ± 0.7 (-22%) | 29.0 (-25%) | 63.4 ± 1.4 | 1.1 ± 0.3 | 179.7 ± 1.5 | 0.4 ± 0.0 | 324 ± 0 | 7 ± 1 | 204 ± 1 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 135.1 ± 2.0 | 0.9 ± 0.0 | 13.3 ± 0.2 |
| Actuated SUMO | nan ± nan | nan ± nan | 118.9 ± 2.4 (-12%) | 0.6 ± 0.0 | 12.3 ± 0.2 (-8%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 116.0 ± 1.6 (-14%) | 0.5 ± 0.0 | 12.8 ± 0.2 (-4%) |
| rl_ppo_romana_lejer | nan ± nan | nan ± nan | 137.7 ± 3.9 (+2%) | 0.7 ± 0.0 | 12.7 ± 0.2 (-5%) |
| rl_ppo_romana_zn3 | nan ± nan | nan ± nan | 146.7 ± 4.2 (+9%) | 0.9 ± 0.1 | 13.3 ± 0.3 (-1%) |

## Scenariul `zi_2026-10-25_varf`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 237.8 ± 25.2 | 236.3 | 322.1 ± 25.7 | 123.9 ± 13.9 | 441.3 ± 24.4 | 35.1 ± 2.4 | 3235 ± 104 | 822 ± 102 | 3179 ± 119 |
| Actuated SUMO | 185.8 ± 82.0 (-22%) | 159.3 (-33%) | 261.3 ± 82.6 | 122.4 ± 28.7 | 383.1 ± 78.2 | 30.8 ± 6.2 | 3381 ± 255 | 708 ± 276 | 2862 ± 292 |
| Agent RL (PPO) | 181.7 ± 33.5 (-24%) | 200.0 (-15%) | 264.6 ± 37.0 | 168.0 ± 10.8 | 387.6 ± 36.4 | 30.5 ± 3.8 | 3390 ± 75 | 713 ± 133 | 2936 ± 171 |
| rl_ppo_romana_lejer | 251.6 ± 107.7 (+6%) | 249.5 (+6%) | 337.1 ± 112.4 | 162.5 ± 12.9 | 459.6 ± 110.8 | 34.4 ± 9.7 | 3223 ± 240 | 959 ± 386 | 3251 ± 521 |
| rl_ppo_romana_zn3 | 185.2 ± 74.9 (-22%) | 142.5 (-40%) | 264.6 ± 77.5 | 154.3 ± 12.5 | 386.8 ± 75.1 | 28.4 ± 8.3 | 3329 ± 232 | 900 ± 399 | 2896 ± 333 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 111.7 ± 30.2 | 162.5 ± 34.7 | 175.5 ± 7.3 | 13.5 ± 1.1 | 534.0 ± 21.3 |
| Actuated SUMO | 152.1 ± 127.4 | 196.5 ± 134.8 | 224.3 ± 24.4 (+28%) | 27.5 ± 5.3 | 500.6 ± 54.5 (-6%) |
| Agent RL (PPO) | 142.2 ± 43.9 | 192.1 ± 47.9 | 199.6 ± 10.8 (+14%) | 20.8 ± 4.5 | 537.9 ± 33.9 (+1%) |
| rl_ppo_romana_lejer | 361.3 ± 161.3 | 421.8 ± 165.8 | 239.2 ± 76.5 (+36%) | 23.8 ± 11.1 | 616.4 ± 139.7 (+15%) |
| rl_ppo_romana_zn3 | 225.3 ± 176.0 | 279.5 ± 178.7 | 237.6 ± 40.4 (+35%) | 34.1 ± 18.8 | 543.3 ± 78.2 (+2%) |

## Scenariul `zi_2026-10-25_varf_x1_2`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 350.3 ± 25.6 | 354.4 | 437.8 ± 26.0 | 190.3 ± 15.8 | 551.6 ± 25.3 | 41.7 ± 1.7 | 3394 ± 79 | 1482 ± 73 | 4045 ± 103 |
| Actuated SUMO | 318.3 ± 20.4 (-9%) | 312.6 (-12%) | 407.0 ± 20.0 | 169.2 ± 20.5 | 523.0 ± 19.5 | 39.0 ± 2.6 | 3509 ± 72 | 1389 ± 150 | 3969 ± 80 |
| Agent RL (PPO) | 338.0 ± 28.8 (-4%) | 348.1 (-2%) | 429.4 ± 28.0 | 174.0 ± 37.7 | 545.4 ± 25.9 | 41.2 ± 3.2 | 3347 ± 150 | 1697 ± 225 | 4066 ± 110 |
| rl_ppo_romana_lejer | 287.4 ± 33.3 (-18%) | 282.4 (-20%) | 378.1 ± 36.6 | 224.6 ± 13.9 | 498.5 ± 35.6 | 38.2 ± 4.1 | 3576 ± 139 | 1310 ± 176 | 3948 ± 165 |
| rl_ppo_romana_zn3 | 343.6 ± 61.6 (-2%) | 345.0 (-3%) | 434.6 ± 59.5 | 193.7 ± 33.7 | 551.6 ± 55.9 | 42.7 ± 6.4 | 3341 ± 263 | 1878 ± 365 | 4077 ± 192 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 267.3 ± 119.8 | 327.0 ± 130.2 | 196.8 ± 26.4 | 13.4 ± 1.3 | 774.7 ± 37.0 |
| Actuated SUMO | 123.0 ± 23.8 | 168.7 ± 29.1 | 241.4 ± 37.9 (+23%) | 22.5 ± 0.7 | 755.4 ± 32.0 (-2%) |
| Agent RL (PPO) | 304.2 ± 93.6 | 368.0 ± 95.9 | 234.5 ± 30.5 (+19%) | 34.8 ± 8.8 | 775.9 ± 51.0 (+0%) |
| rl_ppo_romana_lejer | 362.8 ± 49.3 | 419.2 ± 48.1 | 195.5 ± 7.5 (-1%) | 21.9 ± 2.7 | 776.0 ± 34.6 (+0%) |
| rl_ppo_romana_zn3 | 351.2 ± 125.3 | 404.5 ± 125.6 | 301.7 ± 26.8 (+53%) | 62.4 ± 16.8 | 835.2 ± 59.0 (+8%) |
