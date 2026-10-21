# Rezultate – evaluare comparativă

Medii ± abatere standard pe 5 seed-uri SUMO. Procentele sunt față de plan fix de referință. Mediana pe seed-uri este dată separat pentru așteptarea vehiculelor: aproape de saturație, rețeaua poate intra sau nu în blocaj în funcție de seed, iar câteva rulări blocate trag media în sus. Generat automat de `python -m romana.control.evaluate`.


## Scenariul `referinta_aglomerat`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 789.8 ± 154.4 | 869.8 | 880.3 ± 150.3 | 212.6 ± 34.8 | 977.9 ± 144.9 | 59.8 ± 7.3 | 1395 ± 219 | 1514 ± 253 | 3590 ± 301 |
| Plan fix (Webster) | 798.0 ± 158.3 (+1%) | 733.6 (-16%) | 890.2 ± 160.4 | 226.2 ± 32.7 | 988.0 ± 157.0 | 62.5 ± 8.3 | 1384 ± 173 | 1493 ± 187 | 3643 ± 361 |
| Actuated SUMO | 503.4 ± 224.5 (-36%) | 418.9 (-52%) | 600.3 ± 221.3 | 213.4 ± 12.8 | 707.7 ± 212.2 | 48.2 ± 12.9 | 1851 ± 386 | 1014 ± 411 | 2915 ± 533 |
| Max-Pressure | 710.3 ± 124.6 (-10%) | 755.0 (-13%) | 796.5 ± 124.1 | 193.6 ± 11.7 | 894.4 ± 120.0 | 57.5 ± 6.2 | 1440 ± 167 | 1529 ± 188 | 3405 ± 296 |
| Agent RL (PPO) | 204.2 ± 54.1 (-74%) | 168.5 (-81%) | 281.8 ± 60.7 | 217.6 ± 10.7 | 392.9 ± 61.9 | 27.5 ± 9.6 | 2259 ± 102 | 599 ± 105 | 2010 ± 201 |
| Agent RL coridor (PPO) | 494.6 ± 15.0 (-37%) | 487.9 (-44%) | 594.0 ± 13.1 | 280.4 ± 22.2 | 689.4 ± 12.8 | 9.9 ± 0.6 | 1870 ± 26 | 1001 ± 44 | 2749 ± 17 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 806.6 ± 229.9 | 870.6 ± 228.3 | 223.4 ± 57.6 | 11.6 ± 2.4 | 728.3 ± 98.9 |
| Plan fix (Webster) | 880.6 ± 209.0 | 949.5 ± 204.8 | 175.6 ± 23.1 (-21%) | 9.4 ± 2.7 | 731.8 ± 96.0 (+0%) |
| Actuated SUMO | 401.5 ± 243.7 | 463.2 ± 240.9 | 212.9 ± 18.3 (-5%) | 16.1 ± 1.0 | 580.7 ± 117.7 (-20%) |
| Max-Pressure | 727.5 ± 171.7 | 785.2 ± 173.9 | 237.2 ± 36.6 (+6%) | 20.1 ± 2.2 | 687.1 ± 79.4 (-6%) |
| Agent RL (PPO) | 123.5 ± 42.7 | 175.1 ± 49.2 | 204.1 ± 14.1 (-9%) | 14.0 ± 1.1 | 405.3 ± 34.5 (-44%) |
| Agent RL coridor (PPO) | 217.7 ± 16.9 | 262.8 ± 16.8 | 245.2 ± 33.5 (+10%) | 10.5 ± 0.5 | 624.0 ± 16.9 (-14%) |

## Scenariul `referinta_moderat`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 134.7 ± 22.2 | 121.6 | 195.5 ± 26.4 | 97.3 ± 11.5 | 307.5 ± 26.4 | 10.1 ± 3.9 | 1554 ± 4 | 104 ± 4 | 1138 ± 70 |
| Plan fix (Webster) | 385.1 ± 282.2 (+186%) | 273.9 (+125%) | 460.1 ± 295.7 | 98.7 ± 12.2 | 566.9 ± 290.9 | 32.2 ± 22.2 | 1325 ± 244 | 345 ± 257 | 1701 ± 616 |
| Actuated SUMO | 135.4 ± 33.6 (+1%) | 116.4 (-4%) | 195.4 ± 38.0 | 95.3 ± 12.7 | 307.5 ± 38.2 | 11.9 ± 5.5 | 1555 ± 3 | 104 ± 5 | 1133 ± 98 |
| Max-Pressure | 156.1 ± 60.3 (+16%) | 122.1 (+0%) | 225.3 ± 73.8 | 95.6 ± 22.9 | 337.5 ± 74.1 | 12.8 ± 7.1 | 1558 ± 4 | 97 ± 6 | 1223 ± 192 |
| Agent RL (PPO) | 121.1 ± 24.7 (-10%) | 106.2 (-13%) | 181.1 ± 30.0 | 87.1 ± 7.6 | 293.2 ± 29.9 | 7.7 ± 5.0 | 1556 ± 4 | 127 ± 29 | 1103 ± 78 |
| Agent RL coridor (PPO) | 431.6 ± 74.6 (+220%) | 475.2 (+291%) | 524.7 ± 71.9 | 126.2 ± 6.7 | 625.1 ± 69.5 | 4.9 ± 1.9 | 1344 ± 59 | 360 ± 31 | 1865 ± 144 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 77.8 ± 39.1 | 114.5 ± 42.7 | 152.8 ± 2.0 | 7.2 ± 0.3 | 183.0 ± 17.7 |
| Plan fix (Webster) | 446.0 ± 407.9 | 500.7 ± 421.5 | 145.2 ± 21.8 (-5%) | 5.4 ± 1.6 | 291.5 ± 127.9 (+59%) |
| Actuated SUMO | 84.8 ± 57.8 | 120.7 ± 64.8 | 174.2 ± 8.0 (+14%) | 10.9 ± 1.3 | 189.2 ± 25.7 (+3%) |
| Max-Pressure | 102.4 ± 68.2 | 147.8 ± 78.2 | 141.3 ± 14.5 (-8%) | 5.7 ± 1.9 | 192.2 ± 49.0 (+5%) |
| Agent RL (PPO) | 60.9 ± 38.4 | 96.9 ± 43.5 | 170.6 ± 26.3 (+12%) | 9.2 ± 1.6 | 177.8 ± 25.4 (-3%) |
| Agent RL coridor (PPO) | 203.4 ± 61.5 | 240.9 ± 62.5 | 211.3 ± 9.3 (+38%) | 10.2 ± 0.5 | 361.0 ± 34.0 (+97%) |

## Scenariul `referinta_varf`

**Vehicule motorizate**

| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | Întârziere la intrarea în rețea (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|---|---|
| Plan fix de referință | 401.7 ± 158.8 | 413.2 | 483.9 ± 160.0 | 180.1 ± 11.1 | 591.1 ± 158.0 | 35.5 ± 10.2 | 1712 ± 271 | 677 ± 293 | 2248 ± 355 |
| Plan fix (Webster) | 530.4 ± 362.5 (+32%) | 433.2 (+5%) | 612.7 ± 369.0 | 176.6 ± 24.8 | 716.4 ± 362.8 | 43.8 ± 18.3 | 1549 ± 398 | 859 ± 438 | 2507 ± 790 |
| Actuated SUMO | 260.6 ± 61.4 (-35%) | 254.7 (-38%) | 341.3 ± 69.2 | 212.8 ± 31.8 | 453.9 ± 70.0 | 30.1 ± 5.5 | 1952 ± 102 | 428 ± 123 | 1910 ± 187 |
| Max-Pressure | 306.6 ± 235.6 (-24%) | 174.1 (-58%) | 380.3 ± 235.6 | 179.7 ± 13.3 | 487.2 ± 229.5 | 29.6 ± 18.5 | 1833 ± 365 | 569 ± 429 | 1972 ± 575 |
| Agent RL (PPO) | 149.6 ± 20.5 (-63%) | 138.2 (-67%) | 216.5 ± 25.8 | 184.7 ± 6.9 | 327.1 ± 25.9 | 16.0 ± 3.7 | 2066 ± 17 | 308 ± 20 | 1547 ± 81 |
| Agent RL coridor (PPO) | 528.3 ± 9.2 (+32%) | 532.0 (+29%) | 628.8 ± 14.0 | 237.9 ± 11.1 | 725.8 ± 14.9 | 9.1 ± 4.4 | 1646 ± 46 | 775 ± 18 | 2566 ± 118 |

**Bicicliști, pietoni și total**

| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | Pierdere totală, toți participanții (h) |
|---|---|---|---|---|---|
| Plan fix de referință | 401.7 ± 208.0 | 458.5 ± 206.4 | 168.0 ± 13.6 | 8.8 ± 1.5 | 432.3 ± 74.9 |
| Plan fix (Webster) | 513.2 ± 365.5 | 567.6 ± 368.8 | 163.8 ± 52.1 (-2%) | 7.5 ± 3.5 | 481.6 ± 189.3 (+11%) |
| Actuated SUMO | 196.3 ± 80.6 | 247.6 ± 85.0 | 197.7 ± 14.0 (+18%) | 14.8 ± 1.7 | 386.1 ± 40.8 (-11%) |
| Max-Pressure | 247.0 ± 244.2 | 293.7 ± 242.8 | 173.3 ± 46.2 (+3%) | 10.8 ± 6.9 | 379.1 ± 129.6 (-12%) |
| Agent RL (PPO) | 71.6 ± 24.0 | 111.2 ± 27.0 | 178.0 ± 8.7 (+6%) | 11.1 ± 1.4 | 298.6 ± 21.0 (-31%) |
| Agent RL coridor (PPO) | 200.4 ± 18.1 | 243.7 ± 22.1 | 252.5 ± 31.5 (+50%) | 10.6 ± 0.5 | 563.8 ± 27.5 (+30%) |
