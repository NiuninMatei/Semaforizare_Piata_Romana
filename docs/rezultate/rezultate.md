# Rezultate – evaluare comparativă

Medii ± abatere standard pe 3 seed-uri SUMO. Procentele sunt față de plan fix de referință. Mediana pe seed-uri este dată separat pentru așteptarea vehiculelor: aproape de saturație, rețeaua poate intra sau nu în blocaj în funcție de seed, iar câteva rulări blocate trag media în sus. Generat automat de `python -m romana.control.evaluate`.


## Scenariul `zi_2026-10-21_linistit`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 44.9 ± 0.7 | 45.2 | 83.3 ± 0.7 | 1.4 ± 0.1 | 206.7 ± 0.4 | 3.7 ± 0.1 | 896 ± 0 | 12 ± 4 | 489 ± 2 |
| Max-Pressure | 37.8 ± 0.7 (-16%) | 37.7 (-17%) | 76.5 ± 1.2 | 1.4 ± 0.4 | 199.9 ± 1.2 | 2.3 ± 0.2 | 896 ± 0 | 14 ± 2 | 484 ± 3 |
| Agent RL (PPO) | 40.6 ± 0.6 (-9%) | 40.5 (-10%) | 80.1 ± 0.8 | 1.1 ± 0.1 | 203.5 ± 1.3 | 2.5 ± 0.1 | 896 ± 0 | 13 ± 3 | 490 ± 3 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 136.9 ± 2.0 | 1.2 ± 0.0 | 30.5 ± 0.3 |
| Max-Pressure | nan ± nan | nan ± nan | 128.7 ± 8.0 (-6%) | 0.8 ± 0.3 | 28.2 ± 0.5 (-7%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 116.8 ± 1.7 (-15%) | 0.7 ± 0.0 | 28.2 ± 0.1 (-7%) |

## Scenariul `zi_2026-10-21_linistit_x0_8`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 44.6 ± 0.5 | 44.6 | 82.6 ± 0.7 | 1.2 ± 0.2 | 206.0 ± 1.0 | 3.0 ± 0.1 | 712 ± 0 | 9 ± 2 | 396 ± 0 |
| Max-Pressure | 38.8 ± 0.5 (-13%) | 38.6 (-13%) | 76.8 ± 0.9 | 1.1 ± 0.2 | 200.3 ± 0.9 | 1.7 ± 0.1 | 712 ± 0 | 9 ± 2 | 392 ± 2 |
| Agent RL (PPO) | 40.7 ± 1.1 (-9%) | 41.1 (-8%) | 79.1 ± 1.3 | 0.9 ± 0.2 | 202.6 ± 1.6 | 2.0 ± 0.1 | 712 ± 0 | 9 ± 3 | 395 ± 3 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 136.1 ± 2.0 | 1.2 ± 0.1 | 25.9 ± 0.2 |
| Max-Pressure | nan ± nan | nan ± nan | 122.0 ± 1.6 (-10%) | 0.7 ± 0.0 | 23.8 ± 0.1 (-8%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 116.7 ± 2.3 (-14%) | 0.7 ± 0.1 | 23.8 ± 0.4 (-8%) |

## Scenariul `zi_2026-10-21_pranz`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 88.1 ± 19.7 | 83.0 | 142.4 ± 25.4 | 73.9 ± 10.6 | 263.7 ± 26.5 | 10.8 ± 0.5 | 1856 ± 31 | 447 ± 114 | 1343 ± 57 |
| Max-Pressure | 339.8 ± 71.3 (+286%) | 307.8 (+271%) | 412.3 ± 66.8 | 36.1 ± 7.1 | 528.2 ± 65.8 | 27.2 ± 5.4 | 1558 ± 117 | 710 ± 241 | 2023 ± 133 |
| Agent RL (PPO) | 128.6 ± 16.2 (+46%) | 124.6 (+50%) | 196.2 ± 18.9 | 72.3 ± 11.6 | 318.1 ± 18.8 | 11.7 ± 0.2 | 1843 ± 4 | 209 ± 27 | 1508 ± 60 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 46.4 ± 9.3 | 80.6 ± 9.3 | 222.3 ± 25.4 | 24.5 ± 1.5 | 307.6 ± 15.3 |
| Max-Pressure | 138.7 ± 142.1 | 181.7 ± 150.4 | 176.0 ± 21.8 (-21%) | 17.4 ± 5.3 | 377.0 ± 37.1 (+23%) |
| Agent RL (PPO) | 49.3 ± 7.0 | 87.7 ± 9.5 | 133.3 ± 2.5 (-40%) | 11.7 ± 0.8 | 255.9 ± 17.8 (-17%) |

## Scenariul `zi_2026-10-21_varf`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 490.4 ± 66.2 | 464.6 | 602.8 ± 68.9 | 102.9 ± 19.5 | 714.4 ± 66.5 | 39.9 ± 1.8 | 2140 ± 116 | 1135 ± 128 | 3505 ± 161 |
| Max-Pressure | 876.4 ± 210.2 (+79%) | 884.4 (+90%) | 984.4 ± 196.5 | 113.4 ± 40.2 | 1090.3 ± 197.2 | 53.2 ± 12.6 | 1556 ± 293 | 1837 ± 607 | 4218 ± 227 |
| Agent RL (PPO) | 786.7 ± 194.6 (+60%) | 826.4 (+78%) | 889.1 ± 180.8 | 118.7 ± 1.4 | 997.8 ± 178.7 | 50.7 ± 8.6 | 1682 ± 326 | 2033 ± 566 | 4032 ± 235 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 373.8 ± 32.9 | 440.1 ± 30.5 | 209.5 ± 22.1 | 23.0 ± 3.3 | 695.4 ± 57.7 |
| Max-Pressure | 824.4 ± 360.1 | 896.4 ± 355.9 | 244.1 ± 69.6 (+17%) | 25.4 ± 6.4 | 895.6 ± 139.1 (+29%) |
| Agent RL (PPO) | 796.6 ± 184.9 | 879.9 ± 173.6 | 325.0 ± 31.5 (+55%) | 88.3 ± 29.1 | 929.4 ± 92.3 (+34%) |

## Scenariul `zi_2026-10-21_varf_x1_2`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 589.2 ± 37.0 | 576.1 | 722.1 ± 33.6 | 200.7 ± 15.7 | 829.3 ± 31.9 | 43.8 ± 2.5 | 2312 ± 126 | 1660 ± 251 | 4437 ± 63 |
| Max-Pressure | 857.8 ± 90.7 (+46%) | 881.4 (+53%) | 981.7 ± 80.6 | 266.9 ± 57.0 | 1087.1 ± 79.9 | 56.7 ± 5.4 | 1840 ± 175 | 1923 ± 141 | 4827 ± 71 |
| Agent RL (PPO) | 919.2 ± 137.5 (+56%) | 907.5 (+58%) | 1024.9 ± 131.1 | 210.6 ± 86.7 | 1131.6 ± 129.5 | 60.0 ± 2.9 | 1721 ± 209 | 2760 ± 472 | 4849 ± 113 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 394.2 ± 34.4 | 467.9 ± 28.5 | 256.1 ± 32.1 | 21.2 ± 0.7 | 975.4 ± 23.5 |
| Max-Pressure | 731.6 ± 211.9 | 824.6 ± 212.8 | 231.0 ± 33.2 (-10%) | 27.3 ± 3.6 | 1086.8 ± 27.1 (+11%) |
| Agent RL (PPO) | 961.9 ± 87.7 | 1039.1 ± 90.1 | 392.9 ± 33.0 (+53%) | 102.8 ± 26.7 | 1197.7 ± 115.1 (+23%) |

## Scenariul `zi_2026-10-22_dimineata`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 189.6 ± 38.0 | 205.9 | 274.9 ± 40.6 | 60.1 ± 5.4 | 398.9 ± 38.1 | 12.5 ± 0.3 | 2149 ± 28 | 375 ± 130 | 2102 ± 134 |
| Max-Pressure | 304.8 ± 59.0 (+61%) | 309.1 (+50%) | 413.7 ± 56.9 | 91.8 ± 16.5 | 533.9 ± 54.9 | 24.6 ± 4.2 | 2067 ± 85 | 457 ± 163 | 2587 ± 141 |
| Agent RL (PPO) | 265.6 ± 63.4 (+40%) | 245.4 (+19%) | 360.8 ± 54.8 | 70.2 ± 12.9 | 483.8 ± 52.5 | 16.6 ± 1.0 | 2087 ± 119 | 488 ± 190 | 2384 ± 99 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 99.3 ± 5.9 | 142.6 ± 6.6 | 220.1 ± 57.1 | 24.7 ± 6.9 | 397.9 ± 61.2 |
| Max-Pressure | 134.3 ± 47.1 | 189.9 ± 57.1 | 170.2 ± 23.6 (-23%) | 14.0 ± 2.7 | 462.5 ± 58.2 (+16%) |
| Agent RL (PPO) | 183.9 ± 80.1 | 230.4 ± 79.8 | 203.4 ± 42.4 (-8%) | 14.9 ± 1.7 | 441.3 ± 55.3 (+11%) |

## Scenariul `zi_2026-10-22_linistit`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 46.2 ± 2.1 | 46.3 | 80.9 ± 2.9 | 0.5 ± 0.0 | 206.7 ± 2.8 | 1.2 ± 0.1 | 314 ± 0 | 0 ± 0 | 196 ± 2 |
| Max-Pressure | 37.5 ± 1.2 (-19%) | 37.2 (-20%) | 71.2 ± 2.0 | 1.3 ± 0.6 | 197.0 ± 1.9 | 0.4 ± 0.0 | 314 ± 0 | 0 ± 0 | 190 ± 2 |
| Agent RL (PPO) | 39.9 ± 1.5 (-14%) | 39.6 (-14%) | 75.3 ± 2.4 | 0.5 ± 0.0 | 201.1 ± 2.0 | 0.7 ± 0.1 | 314 ± 0 | 0 ± 0 | 194 ± 2 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 146.3 ± 9.4 | 0.1 ± 0.0 | 7.9 ± 0.2 |
| Max-Pressure | nan ± nan | nan ± nan | 229.5 ± 11.4 (+57%) | 0.1 ± 0.0 | 7.6 ± 0.1 (-4%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 125.7 ± 6.3 (-14%) | 0.1 ± 0.0 | 7.3 ± 0.2 (-8%) |

## Scenariul `zi_2026-10-22_linistit_x0_8`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 47.3 ± 1.3 | 47.9 | 82.3 ± 1.5 | 0.7 ± 0.1 | 208.6 ± 0.8 | 1.0 ± 0.0 | 254 ± 0 | 1 ± 0 | 161 ± 0 |
| Max-Pressure | 35.7 ± 2.8 (-25%) | 36.0 (-25%) | 69.1 ± 3.6 | 0.5 ± 0.0 | 195.4 ± 3.4 | 0.3 ± 0.0 | 254 ± 0 | 1 ± 0 | 155 ± 2 |
| Agent RL (PPO) | 40.3 ± 0.5 (-15%) | 40.3 (-16%) | 75.7 ± 0.3 | 0.6 ± 0.0 | 202.0 ± 1.2 | 0.7 ± 0.0 | 254 ± 0 | 1 ± 0 | 160 ± 1 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 159.7 ± 6.9 | 0.1 ± 0.0 | 6.7 ± 0.1 |
| Max-Pressure | nan ± nan | nan ± nan | 213.1 ± 11.2 (+33%) | 0.1 ± 0.0 | 6.1 ± 0.2 (-10%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 133.9 ± 0.9 (-16%) | 0.1 ± 0.0 | 6.1 ± 0.0 (-9%) |

## Scenariul `zi_2026-10-22_varf`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 132.7 ± 29.6 | 119.5 | 213.3 ± 32.1 | 63.7 ± 4.7 | 341.6 ± 31.6 | 19.2 ± 4.1 | 2509 ± 9 | 458 ± 247 | 2216 ± 150 |
| Max-Pressure | 266.8 ± 26.6 (+101%) | 272.4 (+128%) | 378.0 ± 29.0 | 26.1 ± 10.8 | 503.1 ± 27.8 | 29.5 ± 1.5 | 2285 ± 23 | 586 ± 93 | 2800 ± 108 |
| Agent RL (PPO) | 279.6 ± 55.2 (+111%) | 292.3 (+145%) | 376.6 ± 46.6 | 26.4 ± 19.0 | 502.1 ± 42.3 | 26.1 ± 0.2 | 2245 ± 141 | 685 ± 274 | 2740 ± 121 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 181.2 ± 25.6 | 23.1 ± 1.0 | 341.4 ± 39.9 |
| Max-Pressure | nan ± nan | nan ± nan | 155.2 ± 6.4 (-14%) | 15.6 ± 0.7 | 402.4 ± 19.5 (+18%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 180.6 ± 31.4 (-0%) | 23.0 ± 4.5 | 420.3 ± 42.0 (+23%) |

## Scenariul `zi_2026-10-22_varf_x1_2`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 262.3 ± 32.1 | 245.9 | 384.0 ± 27.9 | 72.0 ± 4.1 | 510.0 ± 27.0 | 28.1 ± 0.9 | 2810 ± 87 | 566 ± 133 | 3416 ± 101 |
| Max-Pressure | 422.1 ± 38.1 (+61%) | 416.6 (+69%) | 560.5 ± 34.0 | 74.8 ± 17.3 | 679.1 ± 30.5 | 35.2 ± 2.8 | 2459 ± 146 | 931 ± 193 | 4069 ± 108 |
| Agent RL (PPO) | 342.3 ± 42.9 (+31%) | 323.9 (+32%) | 478.7 ± 31.7 | 59.0 ± 18.3 | 601.4 ± 27.9 | 30.8 ± 1.0 | 2630 ± 194 | 820 ± 362 | 3771 ± 95 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | nan ± nan | nan ± nan | 183.1 ± 9.6 | 23.8 ± 5.2 | 526.0 ± 26.1 |
| Max-Pressure | nan ± nan | nan ± nan | 171.7 ± 17.2 (-6%) | 15.9 ± 2.3 | 649.0 ± 22.3 (+23%) |
| Agent RL (PPO) | nan ± nan | nan ± nan | 177.6 ± 6.0 (-3%) | 30.7 ± 8.8 | 579.9 ± 18.1 (+10%) |
