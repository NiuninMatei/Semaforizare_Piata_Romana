# Rezultate – evaluare comparativă

Medii ± abatere standard pe 1 seed-uri SUMO. Generat automat de `python -m romana.control.evaluate`.


## Scenariul `referinta_varf`

| Strategie | Așteptare medie (s) | Pierdere de timp (s) | Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |
|---|---|---|---|---|---|---|---|
| Actuated SUMO | 281.7 ± nan (-1%) | 350.0 ± nan | 457.4 ± nan | 33.3 ± nan | 2981 ± nan | 432 ± nan | 2969 ± nan |
| Plan fix (Webster) | 283.4 ± nan | 356.3 ± nan | 463.3 ± nan | 38.0 ± nan | 2938 ± nan | 475 ± nan | 3005 ± nan |
| Max-Pressure | 288.6 ± nan (+2%) | 364.5 ± nan | 471.6 ± nan | 31.6 ± nan | 2949 ± nan | 464 ± nan | 3013 ± nan |
