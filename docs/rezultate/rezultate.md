# Rezultate – evaluare comparativă

*Conține informații din OpenStreetMap (https://www.openstreetmap.org), puse la dispoziție aici sub Open Database License (ODbL) 1.0 – https://opendatacommons.org/licenses/odbl/1-0/. © OpenStreetMap contributors – https://www.openstreetmap.org/copyright*

Medii ± abatere standard pe 10 seed-uri SUMO. Procentele sunt față de plan fix de referință. Mediana pe seed-uri este dată separat pentru așteptarea vehiculelor: aproape de saturație, rețeaua poate intra sau nu în blocaj în funcție de seed, iar câteva rulări blocate trag media în sus. Generat automat de `python -m romana.control.evaluate`.


## Scenariul `zi_2026-10-21_linistit`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 36.8 ± 1.4 | 36.9 | 70.8 ± 1.9 | 2.1 ± 0.6 | 183.0 ± 1.7 | 2.6 ± 0.2 | 692 ± 0 | 8 ± 2 | 337 ± 3 |
| Actuated SUMO | 33.5 ± 0.5 (-9%) | 33.6 (-9%) | 67.5 ± 0.9 | 1.6 ± 0.2 | 179.7 ± 1.1 | 2.1 ± 0.1 | 692 ± 0 | 7 ± 2 | 333 ± 2 |
| Max-Pressure | 32.1 ± 1.2 (-13%) | 32.4 (-12%) | 66.0 ± 1.7 | 1.5 ± 0.4 | 178.2 ± 1.4 | 1.6 ± 0.1 | 692 ± 0 | 8 ± 4 | 332 ± 3 |
| Agent RL (PPO) | 37.9 ± 0.7 (+3%) | 38.1 (+3%) | 73.3 ± 1.0 | 1.3 ± 0.2 | 185.5 ± 1.2 | 2.1 ± 0.1 | 692 ± 0 | 8 ± 3 | 341 ± 2 |
| plan_46_48_12 | 44.5 ± 0.8 (+21%) | 44.5 (+21%) | 79.2 ± 1.1 | 2.7 ± 0.5 | 191.5 ± 1.5 | 3.6 ± 0.1 | 692 ± 0 | 9 ± 3 | 346 ± 2 |
| rl_ppo_romana_lejer | 28.4 ± 1.0 (-23%) | 28.2 (-24%) | 61.5 ± 1.4 | 1.7 ± 0.6 | 173.7 ± 1.2 | 1.1 ± 0.1 | 692 ± 0 | 7 ± 3 | 326 ± 3 |
| rl_ppo_romana_zn3 | 26.7 ± 0.6 (-27%) | 26.6 (-28%) | 59.5 ± 1.1 | 3.4 ± 1.8 | 171.7 ± 1.3 | 1.0 ± 0.1 | 692 ± 0 | 9 ± 2 | 324 ± 2 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 132.4 ± 1.9 | 1.2 ± 0.1 | 23.1 ± 0.3 |
| Actuated SUMO | nan ± nan | nan ± nan | 122.7 ± 2.7 (-7%) | 0.9 ± 0.1 | 21.7 ± 0.2 (-6%) |
| Max-Pressure | nan ± nan | nan ± nan | 120.8 ± 3.1 (-9%) | 0.8 ± 0.1 | 21.3 ± 0.1 (-8%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 113.5 ± 2.7 (-14%) | 0.7 ± 0.1 | 22.1 ± 0.2 (-4%) |
| plan_46_48_12 | nan ± nan | nan ± nan | 150.0 ± 1.6 (+13%) | 1.7 ± 0.1 | 26.0 ± 0.3 (+13%) |
| rl_ppo_romana_lejer | nan ± nan | nan ± nan | 128.4 ± 0.9 (-3%) | 1.0 ± 0.1 | 20.9 ± 0.2 (-9%) |
| rl_ppo_romana_zn3 | nan ± nan | nan ± nan | 147.1 ± 4.0 (+11%) | 1.5 ± 0.1 | 22.2 ± 0.5 (-4%) |

## Scenariul `zi_2026-10-21_linistit_x0_8`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 37.0 ± 1.3 | 36.9 | 69.5 ± 1.8 | 1.5 ± 0.3 | 181.3 ± 1.9 | 2.1 ± 0.1 | 555 ± 0 | 9 ± 2 | 266 ± 3 |
| Actuated SUMO | 33.1 ± 0.8 (-10%) | 33.2 (-10%) | 65.6 ± 0.9 | 1.1 ± 0.2 | 177.4 ± 1.3 | 1.5 ± 0.1 | 555 ± 0 | 9 ± 2 | 263 ± 2 |
| Max-Pressure | 31.9 ± 0.8 (-14%) | 31.8 (-14%) | 64.8 ± 1.4 | 1.4 ± 0.6 | 176.6 ± 0.9 | 1.2 ± 0.1 | 555 ± 0 | 10 ± 1 | 263 ± 2 |
| Agent RL (PPO) | 36.7 ± 0.7 (-1%) | 36.9 (+0%) | 71.1 ± 0.9 | 1.0 ± 0.2 | 183.0 ± 1.6 | 1.4 ± 0.1 | 555 ± 0 | 10 ± 1 | 271 ± 1 |
| plan_46_48_12 | 44.7 ± 1.4 (+21%) | 44.4 (+20%) | 77.6 ± 1.5 | 2.0 ± 0.4 | 189.5 ± 1.9 | 3.0 ± 0.1 | 555 ± 0 | 11 ± 1 | 273 ± 2 |
| rl_ppo_romana_lejer | 28.8 ± 0.6 (-22%) | 28.7 (-22%) | 60.1 ± 0.9 | 1.4 ± 0.3 | 171.9 ± 1.0 | 0.8 ± 0.0 | 555 ± 0 | 10 ± 1 | 257 ± 1 |
| rl_ppo_romana_zn3 | 27.3 ± 0.5 (-26%) | 27.4 (-26%) | 59.2 ± 0.6 | 2.1 ± 0.4 | 170.9 ± 0.7 | 0.8 ± 0.1 | 555 ± 0 | 10 ± 1 | 258 ± 1 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 137.7 ± 2.2 | 1.2 ± 0.1 | 20.4 ± 0.4 |
| Actuated SUMO | nan ± nan | nan ± nan | 125.3 ± 2.0 (-9%) | 0.9 ± 0.1 | 18.9 ± 0.2 (-7%) |
| Max-Pressure | nan ± nan | nan ± nan | 126.0 ± 2.9 (-8%) | 0.7 ± 0.1 | 18.8 ± 0.1 (-8%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 119.2 ± 2.4 (-13%) | 0.8 ± 0.1 | 19.3 ± 0.2 (-5%) |
| plan_46_48_12 | nan ± nan | nan ± nan | 156.1 ± 3.5 (+13%) | 1.9 ± 0.2 | 23.0 ± 0.4 (+13%) |
| rl_ppo_romana_lejer | nan ± nan | nan ± nan | 131.2 ± 0.9 (-5%) | 0.9 ± 0.1 | 18.5 ± 0.2 (-9%) |
| rl_ppo_romana_zn3 | nan ± nan | nan ± nan | 150.0 ± 4.2 (+9%) | 1.4 ± 0.1 | 19.7 ± 0.4 (-3%) |

## Scenariul `zi_2026-10-21_pranz`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 92.8 ± 25.0 | 86.1 | 147.7 ± 31.7 | 124.5 ± 18.0 | 260.4 ± 31.7 | 10.0 ± 2.1 | 1205 ± 18 | 367 ± 109 | 840 ± 69 |
| Actuated SUMO | 65.9 ± 21.2 (-29%) | 61.2 (-29%) | 110.9 ± 27.1 | 141.4 ± 24.8 | 222.7 ± 26.8 | 7.3 ± 2.3 | 1230 ± 23 | 403 ± 121 | 775 ± 65 |
| Max-Pressure | 432.6 ± 116.0 (+366%) | 490.5 (+470%) | 510.1 ± 121.9 | 77.1 ± 15.4 | 615.4 ± 120.2 | 31.3 ± 6.3 | 1015 ± 83 | 637 ± 192 | 1490 ± 208 |
| Agent RL (PPO) | 124.0 ± 7.7 (+34%) | 120.7 (+40%) | 191.9 ± 9.4 | 126.3 ± 15.6 | 305.4 ± 9.8 | 13.0 ± 0.5 | 1187 ± 13 | 277 ± 78 | 923 ± 14 |
| plan_46_48_12 | 99.8 ± 39.4 (+8%) | 89.7 (+4%) | 149.5 ± 42.9 | 138.7 ± 10.8 | 260.3 ± 43.4 | 11.2 ± 3.2 | 1217 ± 32 | 459 ± 72 | 848 ± 80 |
| rl_ppo_romana_lejer | 143.9 ± 56.8 (+55%) | 121.1 (+41%) | 204.4 ± 57.4 | 123.2 ± 39.1 | 316.1 ± 55.4 | 14.2 ± 5.0 | 1178 ± 61 | 348 ± 190 | 945 ± 86 |
| rl_ppo_romana_zn3 | 196.0 ± 179.5 (+111%) | 123.8 (+44%) | 254.9 ± 185.1 | 102.2 ± 31.0 | 365.7 ± 179.3 | 14.0 ± 10.2 | 1127 ± 123 | 585 ± 402 | 1017 ± 307 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 85.0 ± 31.9 | 129.0 ± 39.0 | 204.1 ± 29.9 | 26.9 ± 6.5 | 271.6 ± 27.7 |
| Actuated SUMO | 61.5 ± 30.1 | 97.8 ± 32.7 | 221.2 ± 40.8 (+8%) | 28.1 ± 5.7 | 281.6 ± 32.9 (+4%) |
| Max-Pressure | 395.8 ± 177.4 | 461.6 ± 182.1 | 180.1 ± 35.9 (-12%) | 18.0 ± 3.1 | 350.8 ± 62.2 (+29%) |
| Agent RL (PPO) | 91.2 ± 10.6 | 141.0 ± 15.5 | 139.3 ± 5.4 (-32%) | 12.2 ± 2.0 | 229.0 ± 3.9 (-16%) |
| plan_46_48_12 | 109.7 ± 70.8 | 152.7 ± 75.5 | 210.7 ± 37.3 (+3%) | 33.5 ± 5.1 | 285.0 ± 29.7 (+5%) |
| rl_ppo_romana_lejer | 111.6 ± 29.3 | 166.2 ± 35.5 | 143.3 ± 9.6 (-30%) | 13.6 ± 3.1 | 236.6 ± 7.0 (-13%) |
| rl_ppo_romana_zn3 | 143.1 ± 172.5 | 192.5 ± 180.8 | 203.7 ± 46.3 (-0%) | 29.4 ± 28.6 | 296.3 ± 80.3 (+9%) |

## Scenariul `zi_2026-10-21_varf`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 224.9 ± 37.8 | 233.4 | 284.7 ± 40.0 | 40.9 ± 12.5 | 397.5 ± 38.9 | 23.9 ± 2.4 | 1615 ± 49 | 557 ± 217 | 1507 ± 104 |
| Actuated SUMO | 197.2 ± 30.5 (-12%) | 202.2 (-13%) | 253.2 ± 29.9 | 32.7 ± 7.8 | 367.4 ± 28.1 | 21.6 ± 2.2 | 1633 ± 57 | 706 ± 158 | 1422 ± 70 |
| Max-Pressure | 539.7 ± 145.6 (+140%) | 514.3 (+120%) | 629.9 ± 151.6 | 68.0 ± 58.1 | 736.3 ± 147.3 | 39.1 ± 5.1 | 1321 ± 158 | 928 ± 332 | 2262 ± 281 |
| Agent RL (PPO) | 393.3 ± 130.0 (+75%) | 377.0 (+62%) | 475.6 ± 133.4 | 44.5 ± 11.2 | 587.0 ± 128.6 | 32.5 ± 4.2 | 1421 ± 130 | 1210 ± 200 | 1908 ± 287 |
| plan_46_48_12 | 225.7 ± 46.9 (+0%) | 252.8 (+8%) | 284.3 ± 47.0 | 37.6 ± 7.8 | 397.7 ± 44.3 | 24.6 ± 3.0 | 1619 ± 66 | 694 ± 181 | 1506 ± 109 |
| rl_ppo_romana_lejer | 321.7 ± 113.8 (+43%) | 346.9 (+49%) | 400.5 ± 115.9 | 42.7 ± 19.5 | 513.8 ± 110.8 | 28.6 ± 5.5 | 1503 ± 164 | 744 ± 384 | 1744 ± 233 |
| rl_ppo_romana_zn3 | 267.0 ± 89.2 (+19%) | 248.1 (+6%) | 335.8 ± 89.3 | 27.5 ± 10.1 | 449.4 ± 85.2 | 27.3 ± 4.2 | 1523 ± 122 | 966 ± 273 | 1591 ± 190 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 280.5 ± 75.2 | 344.6 ± 77.8 | 192.4 ± 33.1 | 23.5 ± 4.8 | 330.7 ± 41.9 |
| Actuated SUMO | 236.7 ± 129.5 | 299.3 ± 138.5 | 233.8 ± 25.0 (+21%) | 37.1 ± 4.8 | 347.9 ± 32.7 (+5%) |
| Max-Pressure | 818.4 ± 209.0 | 913.3 ± 205.6 | 196.7 ± 29.0 (+2%) | 19.5 ± 2.5 | 493.5 ± 104.9 (+49%) |
| Agent RL (PPO) | 510.8 ± 315.7 | 585.6 ± 322.2 | 207.5 ± 36.6 (+8%) | 50.7 ± 20.4 | 425.4 ± 81.1 (+29%) |
| plan_46_48_12 | 251.7 ± 68.1 | 309.0 ± 67.5 | 219.6 ± 20.6 (+14%) | 30.7 ± 5.6 | 353.0 ± 17.9 (+7%) |
| rl_ppo_romana_lejer | 422.8 ± 157.6 | 490.1 ± 162.2 | 194.8 ± 33.3 (+1%) | 22.7 ± 4.8 | 381.0 ± 72.5 (+15%) |
| rl_ppo_romana_zn3 | 474.1 ± 262.0 | 545.4 ± 273.7 | 194.7 ± 23.5 (+1%) | 56.5 ± 17.8 | 344.9 ± 54.3 (+4%) |

## Scenariul `zi_2026-10-21_varf_x1_2`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 357.1 ± 60.6 | 340.9 | 432.1 ± 57.8 | 83.2 ± 32.9 | 541.3 ± 56.0 | 31.3 ± 3.8 | 1805 ± 113 | 814 ± 194 | 2225 ± 90 |
| Actuated SUMO | 334.3 ± 53.1 (-6%) | 330.2 (-3%) | 401.4 ± 54.3 | 80.4 ± 25.3 | 510.2 ± 53.3 | 30.6 ± 2.4 | 1789 ± 68 | 940 ± 149 | 2125 ± 126 |
| Max-Pressure | 646.3 ± 92.1 (+81%) | 631.7 (+85%) | 752.2 ± 91.8 | 109.2 ± 30.6 | 857.9 ± 91.1 | 41.9 ± 3.3 | 1457 ± 107 | 1194 ± 249 | 2949 ± 177 |
| Agent RL (PPO) | 574.2 ± 90.9 (+61%) | 596.4 (+75%) | 666.4 ± 81.0 | 67.4 ± 12.3 | 772.9 ± 78.7 | 39.1 ± 3.1 | 1461 ± 156 | 1557 ± 256 | 2685 ± 149 |
| plan_46_48_12 | 340.2 ± 33.1 (-5%) | 343.8 (+1%) | 410.7 ± 34.2 | 63.7 ± 14.6 | 518.9 ± 33.2 | 31.8 ± 1.4 | 1790 ± 43 | 895 ± 171 | 2168 ± 79 |
| rl_ppo_romana_lejer | 513.1 ± 107.3 (+44%) | 543.4 (+59%) | 614.3 ± 101.8 | 70.6 ± 20.4 | 723.8 ± 95.7 | 34.6 ± 4.6 | 1602 ± 161 | 999 ± 407 | 2678 ± 229 |
| rl_ppo_romana_zn3 | 464.1 ± 159.2 (+30%) | 404.0 (+18%) | 553.9 ± 156.4 | 48.5 ± 21.2 | 663.6 ± 153.4 | 34.9 ± 4.6 | 1589 ± 184 | 1447 ± 375 | 2448 ± 307 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 435.1 ± 128.5 | 507.7 ± 131.8 | 209.6 ± 11.4 | 26.7 ± 5.3 | 480.4 ± 45.3 |
| Actuated SUMO | 440.3 ± 106.8 | 500.8 ± 111.8 | 249.4 ± 21.4 (+19%) | 42.9 ± 4.9 | 497.5 ± 52.9 (+4%) |
| Max-Pressure | 889.2 ± 248.0 | 984.7 ± 248.3 | 204.0 ± 23.4 (-3%) | 18.9 ± 1.8 | 633.5 ± 49.3 (+32%) |
| Agent RL (PPO) | 836.8 ± 194.8 | 913.2 ± 195.2 | 251.3 ± 25.7 (+20%) | 63.1 ± 6.2 | 607.7 ± 47.7 (+26%) |
| plan_46_48_12 | 427.1 ± 138.2 | 488.7 ± 140.7 | 233.4 ± 23.1 (+11%) | 35.6 ± 5.7 | 480.8 ± 42.4 (+0%) |
| rl_ppo_romana_lejer | 745.3 ± 200.1 | 841.4 ± 220.0 | 207.9 ± 18.9 (-1%) | 29.1 ± 6.9 | 557.3 ± 73.2 (+16%) |
| rl_ppo_romana_zn3 | 809.1 ± 211.8 | 893.9 ± 212.2 | 252.2 ± 39.3 (+20%) | 75.7 ± 20.3 | 547.0 ± 107.9 (+14%) |

## Scenariul `zi_2026-10-22_dimineata`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 281.8 ± 85.0 | 274.5 | 353.5 ± 90.2 | 100.2 ± 27.0 | 465.3 ± 88.2 | 25.2 ± 3.4 | 1485 ± 74 | 533 ± 133 | 1609 ± 204 |
| Actuated SUMO | 184.0 ± 111.5 (-35%) | 146.2 (-47%) | 244.4 ± 116.1 | 95.2 ± 20.9 | 357.9 ± 112.7 | 19.8 ± 6.3 | 1599 ± 89 | 561 ± 178 | 1375 ± 282 |
| Max-Pressure | 701.1 ± 200.7 (+149%) | 745.2 (+172%) | 790.4 ± 194.1 | 75.1 ± 23.9 | 890.5 ± 188.2 | 40.7 ± 6.2 | 1082 ± 187 | 962 ± 245 | 2415 ± 296 |
| Agent RL (PPO) | 318.7 ± 84.2 (+13%) | 318.3 (+16%) | 401.2 ± 84.1 | 58.5 ± 22.5 | 513.9 ± 79.8 | 26.3 ± 6.1 | 1377 ± 118 | 695 ± 237 | 1654 ± 157 |
| plan_46_48_12 | 252.4 ± 91.0 (-10%) | 258.5 (-6%) | 315.9 ± 90.7 | 93.3 ± 22.4 | 426.1 ± 85.9 | 25.0 ± 5.1 | 1528 ± 92 | 471 ± 240 | 1545 ± 209 |
| rl_ppo_romana_lejer | 366.5 ± 188.0 (+30%) | 351.6 (+28%) | 450.1 ± 185.0 | 71.4 ± 46.8 | 561.9 ± 180.2 | 28.9 ± 9.7 | 1356 ± 212 | 615 ± 377 | 1757 ± 337 |
| rl_ppo_romana_zn3 | 259.3 ± 163.3 (-8%) | 245.3 (-11%) | 338.5 ± 162.3 | 87.0 ± 46.2 | 451.8 ± 157.2 | 19.2 ± 8.1 | 1437 ± 175 | 636 ± 454 | 1510 ± 316 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 100.8 ± 17.7 | 146.0 ± 22.0 | 232.4 ± 37.6 | 25.7 ± 5.6 | 397.8 ± 45.7 |
| Actuated SUMO | 79.0 ± 40.3 | 117.7 ± 42.5 | 292.0 ± 57.8 (+26%) | 40.5 ± 13.2 | 401.5 ± 81.5 (+1%) |
| Max-Pressure | 405.6 ± 376.3 | 476.7 ± 402.7 | 198.5 ± 19.2 (-15%) | 20.8 ± 3.9 | 519.4 ± 85.8 (+31%) |
| Agent RL (PPO) | 237.6 ± 76.8 | 296.2 ± 80.6 | 211.3 ± 31.7 (-9%) | 28.4 ± 13.9 | 372.7 ± 48.4 (-6%) |
| plan_46_48_12 | 117.8 ± 53.1 | 159.0 ± 54.8 | 224.4 ± 20.2 (-3%) | 33.9 ± 4.5 | 376.5 ± 47.0 (-5%) |
| rl_ppo_romana_lejer | 216.2 ± 95.3 | 270.6 ± 92.7 | 186.7 ± 35.3 (-20%) | 25.7 ± 10.4 | 377.7 ± 79.2 (-5%) |
| rl_ppo_romana_zn3 | 172.1 ± 80.6 | 222.1 ± 80.0 | 210.6 ± 51.5 (-9%) | 33.1 ± 22.0 | 360.5 ± 86.5 (-9%) |

## Scenariul `zi_2026-10-22_linistit`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 40.9 ± 1.3 | 41.2 | 72.1 ± 1.5 | 0.5 ± 0.0 | 191.4 ± 1.6 | 0.6 ± 0.0 | 169 ± 0 | 1 ± 0 | 97 ± 1 |
| Actuated SUMO | 35.9 ± 0.8 (-12%) | 36.2 (-12%) | 68.3 ± 1.1 | 0.6 ± 0.1 | 187.6 ± 1.3 | 0.4 ± 0.0 | 169 ± 0 | 1 ± 0 | 97 ± 1 |
| Max-Pressure | 34.8 ± 1.1 (-15%) | 34.8 (-15%) | 65.9 ± 1.2 | 0.9 ± 0.7 | 185.3 ± 1.4 | 0.2 ± 0.0 | 169 ± 0 | 1 ± 0 | 96 ± 1 |
| Agent RL (PPO) | 32.4 ± 0.8 (-21%) | 32.1 (-22%) | 64.3 ± 1.4 | 0.5 ± 0.0 | 183.7 ± 1.7 | 0.3 ± 0.0 | 169 ± 0 | 1 ± 0 | 96 ± 1 |
| plan_46_48_12 | 43.5 ± 1.3 (+6%) | 43.4 (+5%) | 74.9 ± 1.6 | 0.5 ± 0.0 | 194.3 ± 2.0 | 0.7 ± 0.0 | 169 ± 0 | 1 ± 0 | 98 ± 1 |
| rl_ppo_romana_lejer | 32.0 ± 1.3 (-22%) | 31.4 (-24%) | 61.9 ± 1.6 | 1.3 ± 0.8 | 181.2 ± 1.6 | 0.1 ± 0.0 | 169 ± 0 | 1 ± 0 | 94 ± 1 |
| rl_ppo_romana_zn3 | 27.7 ± 0.8 (-32%) | 27.6 (-33%) | 58.5 ± 1.3 | 0.8 ± 1.0 | 177.8 ± 1.4 | 0.2 ± 0.0 | 169 ± 0 | 1 ± 0 | 94 ± 1 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 120.6 ± 5.8 | 0.1 ± 0.0 | 4.1 ± 0.1 |
| Actuated SUMO | nan ± nan | nan ± nan | 104.4 ± 5.2 (-13%) | 0.0 ± 0.0 | 3.8 ± 0.1 (-7%) |
| Max-Pressure | nan ± nan | nan ± nan | 168.6 ± 19.1 (+40%) | 0.1 ± 0.0 | 4.1 ± 0.1 (-0%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 110.8 ± 4.2 (-8%) | 0.1 ± 0.0 | 3.7 ± 0.1 (-10%) |
| plan_46_48_12 | nan ± nan | nan ± nan | 137.6 ± 6.1 (+14%) | 0.1 ± 0.0 | 4.3 ± 0.1 (+6%) |
| rl_ppo_romana_lejer | nan ± nan | nan ± nan | 189.4 ± 18.6 (+57%) | 0.1 ± 0.0 | 4.0 ± 0.2 (-1%) |
| rl_ppo_romana_zn3 | nan ± nan | nan ± nan | 202.7 ± 27.8 (+68%) | 0.2 ± 0.1 | 3.9 ± 0.2 (-4%) |

## Scenariul `zi_2026-10-22_linistit_x0_8`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 41.0 ± 1.3 | 41.0 | 72.4 ± 1.7 | 0.5 ± 0.0 | 192.2 ± 2.1 | 0.5 ± 0.0 | 136 ± 0 | 0 ± 1 | 81 ± 1 |
| Actuated SUMO | 36.6 ± 1.5 (-11%) | 36.9 (-10%) | 69.4 ± 2.0 | 0.6 ± 0.2 | 189.3 ± 1.5 | 0.3 ± 0.0 | 136 ± 0 | 0 ± 0 | 81 ± 1 |
| Max-Pressure | 34.2 ± 2.1 (-17%) | 34.8 (-15%) | 64.4 ± 2.3 | 1.1 ± 0.4 | 184.0 ± 2.2 | 0.1 ± 0.0 | 136 ± 0 | 1 ± 1 | 79 ± 1 |
| Agent RL (PPO) | 33.3 ± 0.9 (-19%) | 33.2 (-19%) | 64.8 ± 1.5 | 0.5 ± 0.0 | 184.5 ± 2.0 | 0.3 ± 0.0 | 136 ± 0 | 1 ± 1 | 80 ± 1 |
| plan_46_48_12 | 45.9 ± 0.6 (+12%) | 46.1 (+12%) | 77.4 ± 0.8 | 0.5 ± 0.0 | 197.1 ± 1.4 | 0.6 ± 0.0 | 136 ± 0 | 0 ± 0 | 83 ± 0 |
| rl_ppo_romana_lejer | 31.0 ± 1.6 (-24%) | 31.6 (-23%) | 60.8 ± 1.7 | 1.5 ± 0.3 | 180.5 ± 2.5 | 0.1 ± 0.0 | 136 ± 0 | 1 ± 0 | 78 ± 0 |
| rl_ppo_romana_zn3 | 30.9 ± 1.0 (-25%) | 31.1 (-24%) | 62.6 ± 1.1 | 0.5 ± 0.0 | 182.4 ± 1.6 | 0.2 ± 0.0 | 136 ± 0 | 0 ± 1 | 80 ± 1 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 160.1 ± 3.7 | 0.1 ± 0.0 | 3.6 ± 0.1 |
| Actuated SUMO | nan ± nan | nan ± nan | 135.0 ± 6.5 (-16%) | 0.0 ± 0.0 | 3.4 ± 0.1 (-7%) |
| Max-Pressure | nan ± nan | nan ± nan | 314.0 ± 33.9 (+96%) | 0.1 ± 0.0 | 4.2 ± 0.2 (+16%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 158.2 ± 10.2 (-1%) | 0.1 ± 0.0 | 3.3 ± 0.0 (-8%) |
| plan_46_48_12 | nan ± nan | nan ± nan | 184.9 ± 3.8 (+15%) | 0.1 ± 0.0 | 4.0 ± 0.0 (+9%) |
| rl_ppo_romana_lejer | nan ± nan | nan ± nan | 314.5 ± 5.4 (+96%) | 0.1 ± 0.0 | 4.1 ± 0.1 (+13%) |
| rl_ppo_romana_zn3 | nan ± nan | nan ± nan | 239.3 ± 17.0 (+49%) | 0.1 ± 0.0 | 3.7 ± 0.1 (+2%) |

## Scenariul `zi_2026-10-22_varf`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 231.1 ± 69.3 | 227.4 | 295.9 ± 71.9 | 49.0 ± 9.6 | 408.6 ± 68.6 | 22.9 ± 3.9 | 1605 ± 73 | 501 ± 146 | 1643 ± 187 |
| Actuated SUMO | 226.2 ± 106.7 (-2%) | 173.2 (-24%) | 285.2 ± 112.4 | 61.9 ± 31.2 | 398.0 ± 108.1 | 22.3 ± 5.0 | 1587 ± 92 | 663 ± 239 | 1596 ± 287 |
| Max-Pressure | 454.7 ± 87.4 (+97%) | 443.5 (+95%) | 532.6 ± 92.2 | 50.8 ± 16.6 | 639.1 ± 91.2 | 36.4 ± 3.9 | 1330 ± 80 | 838 ± 177 | 2160 ± 202 |
| Agent RL (PPO) | 335.3 ± 168.7 (+45%) | 296.2 (+30%) | 419.5 ± 174.0 | 45.0 ± 12.1 | 534.4 ± 168.6 | 30.5 ± 9.0 | 1470 ± 173 | 823 ± 406 | 1879 ± 375 |
| plan_46_48_12 | 231.2 ± 56.6 (+0%) | 252.5 (+11%) | 288.2 ± 55.5 | 59.1 ± 13.5 | 398.9 ± 51.6 | 23.4 ± 3.1 | 1562 ± 93 | 631 ± 136 | 1598 ± 124 |
| rl_ppo_romana_lejer | 309.1 ± 68.7 (+34%) | 332.5 (+46%) | 382.5 ± 64.6 | 35.1 ± 24.0 | 498.0 ± 61.1 | 29.0 ± 4.6 | 1426 ± 105 | 885 ± 255 | 1758 ± 129 |
| rl_ppo_romana_zn3 | 234.0 ± 106.2 (+1%) | 186.8 (-18%) | 301.6 ± 111.5 | 42.9 ± 18.3 | 416.7 ± 109.4 | 23.7 ± 5.1 | 1545 ± 144 | 865 ± 360 | 1602 ± 237 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 193.3 ± 20.0 | 24.1 ± 3.7 | 322.2 ± 46.1 |
| Actuated SUMO | nan ± nan | nan ± nan | 227.0 ± 30.9 (+17%) | 36.5 ± 5.6 | 349.2 ± 89.3 (+8%) |
| Max-Pressure | nan ± nan | nan ± nan | 173.2 ± 19.2 (-10%) | 17.8 ± 1.7 | 407.4 ± 53.3 (+26%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 187.7 ± 21.9 (-3%) | 35.1 ± 18.3 | 361.1 ± 87.8 (+12%) |
| plan_46_48_12 | nan ± nan | nan ± nan | 213.4 ± 16.1 (+10%) | 33.8 ± 2.2 | 339.1 ± 22.6 (+5%) |
| rl_ppo_romana_lejer | nan ± nan | nan ± nan | 170.8 ± 14.4 (-12%) | 25.1 ± 8.7 | 324.0 ± 27.0 (+1%) |
| rl_ppo_romana_zn3 | nan ± nan | nan ± nan | 188.2 ± 29.3 (-3%) | 44.8 ± 19.1 | 311.0 ± 64.8 (-3%) |

## Scenariul `zi_2026-10-22_varf_x1_2`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 370.1 ± 85.3 | 356.3 | 448.6 ± 88.5 | 90.8 ± 27.2 | 557.5 ± 87.3 | 31.5 ± 4.9 | 1758 ± 117 | 706 ± 202 | 2367 ± 200 |
| Actuated SUMO | 294.0 ± 57.5 (-21%) | 284.7 (-20%) | 364.1 ± 58.6 | 78.5 ± 32.9 | 474.1 ± 56.1 | 28.9 ± 2.7 | 1829 ± 92 | 831 ± 130 | 2147 ± 145 |
| Max-Pressure | 732.2 ± 202.4 (+98%) | 776.6 (+118%) | 823.5 ± 204.1 | 75.3 ± 21.0 | 928.0 ± 201.9 | 48.0 ± 9.2 | 1275 ± 184 | 1319 ± 232 | 3032 ± 397 |
| Agent RL (PPO) | 419.6 ± 77.0 (+13%) | 430.2 (+21%) | 518.8 ± 73.6 | 55.2 ± 14.8 | 631.6 ± 68.9 | 34.1 ± 3.4 | 1632 ± 151 | 1105 ± 273 | 2473 ± 147 |
| plan_46_48_12 | 338.0 ± 30.4 (-9%) | 328.9 (-8%) | 407.3 ± 27.1 | 88.4 ± 11.8 | 514.7 ± 25.7 | 30.1 ± 2.5 | 1767 ± 62 | 765 ± 91 | 2263 ± 39 |
| rl_ppo_romana_lejer | 459.7 ± 49.7 (+24%) | 442.8 (+24%) | 556.0 ± 48.6 | 32.7 ± 16.8 | 666.4 ± 45.6 | 38.2 ± 1.7 | 1516 ± 74 | 1136 ± 156 | 2520 ± 101 |
| rl_ppo_romana_zn3 | 385.7 ± 70.5 (+4%) | 380.8 (+7%) | 474.5 ± 73.0 | 36.9 ± 8.0 | 586.8 ± 70.1 | 35.1 ± 3.8 | 1612 ± 107 | 1349 ± 203 | 2325 ± 171 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 210.3 ± 27.6 | 23.9 ± 5.3 | 468.5 ± 57.1 |
| Actuated SUMO | nan ± nan | nan ± nan | 243.2 ± 28.9 (+16%) | 39.6 ± 7.6 | 447.8 ± 52.3 (-4%) |
| Max-Pressure | nan ± nan | nan ± nan | 214.3 ± 19.2 (+2%) | 23.0 ± 4.2 | 604.9 ± 88.6 (+29%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 213.6 ± 16.3 (+2%) | 44.3 ± 12.7 | 474.5 ± 45.7 (+1%) |
| plan_46_48_12 | nan ± nan | nan ± nan | 216.0 ± 14.1 (+3%) | 35.7 ± 11.8 | 455.2 ± 21.3 (-3%) |
| rl_ppo_romana_lejer | nan ± nan | nan ± nan | 194.5 ± 10.2 (-8%) | 38.3 ± 3.6 | 462.0 ± 36.8 (-1%) |
| rl_ppo_romana_zn3 | nan ± nan | nan ± nan | 223.5 ± 23.9 (+6%) | 73.6 ± 10.6 | 449.1 ± 52.7 (-4%) |

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
