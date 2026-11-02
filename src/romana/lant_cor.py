"""Lanțul măsurii noi (§ 6.5, § 9.11): dintr-o zi colectată, până la scenariile `cor_`, verdictul geamănului față de cameră și rezultatele strategiilor.

Măsura veche rămâne în `romana.lant_zilnic`, neschimbată, doar pentru istoric. Lanțul de aici pornește după ea, fiindcă ea a verificat deja jurnalul zilei și îi lasă prioritatea, și rulează aceiași pași cu fișierele măsurii noi:
  1. renumărarea, pe zonele din `config/camera_v2.json`, pe persoane (`data/counts_cor`);
  2. scenariile `cor_zi_<zi>_*` și variantele cu participanți indisciplinați;
  3. geamănul față de cameră (`valideaza_geaman`), pe orele observate, cu pragurile înghețate, dacă există; verdictul porții intră în `outputs/validare/poarta_cor_<zi>.json`;
  4. dacă rolul zilei o cere, strategiile, cu seed-urile rolului (`validare`), pe ambele comportamente, și regula din § 9.11 (`decizie`), cu cele două referințe și cu poarta.
Zilele de test și de generalizare se opresc înaintea pasului 4 până la --desigileaza. Lista candidaților stă în `config/candidati_v2.json`, cu commit până la termenul din § 9.11; fără ea, pasul de decizie se sare, iar pe zilele de antrenare rulează doar referințele și strategiile raportate.

Ieșirile: outputs/lant_cor/<zi>/ (jurnal.txt, <pas>.txt, stare.json), outputs/validare/geaman_cor_<zi>.csv, poarta_cor_<zi>.json, cor_test_<zi>_{normal,indisciplinat}.csv, cor_decizie_<zi>.json. Nimic nu se copiază singur în docs/.

Rulare:
  python -m romana.lant_cor --zi 2026-11-03
  python -m romana.lant_cor --zi 2026-11-05 --desigileaza --reia
  python -m romana.lant_cor --bucla --ora 03:30 --pana-la "2026-11-08 12:00"
  python -m romana.lant_cor --zi 2026-11-03 --uscat            # doar arată comenzile
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

from romana.common import CONFIG_DIR, DEMAND_DIR, OUTPUT_DIR, ROOT, TRAJ_RAW_DIR
from romana.lant_zilnic import DIR_LANT, PY, ROLURI, ROLURI_SIGILATE, SEEDURI_ROL, SEEDURI_TEST, Pas, _iso, _m, excluderi_zi, noteaza, prioritate_scazuta, ruleaza, uneste, zi_valida

DIR_COR = OUTPUT_DIR / "lant_cor"
CANDIDATI = CONFIG_DIR / "candidati_v2.json"
PRAGURI = ROOT / "docs" / "rezultate" / "praguri_geaman.json"
REFERINTE = ("PLAN_72_48_3", "REAL")
PROCESE_VALIDARE = "3"
PROCESE_TEST = "8"
SEEDURI_GEAMAN = "1,2,3,4,5"
ASTEPTARE_LANT_VECHI_S = 5 * 3600.0     # cât așteaptă după lanțul vechi; după atât pornește oricum, renumărarea lui nu e o condiție
PAS_ASTEPTARE_S = 60.0


def lista_candidati(cale: Path = CANDIDATI) -> list[str]:
    """Candidații din § 9.11, de la cel mai simplu la cel mai complex; lista lipsește până la termen."""
    if not cale.exists():
        return []
    return list(json.loads(cale.read_text(encoding="utf-8")).get("candidati", []))


def strategii_raportate(cale: Path = CANDIDATI) -> list[str]:
    """Strategiile care se raportează lângă candidați și nu pot câștiga."""
    if not cale.exists():
        return []
    return list(json.loads(cale.read_text(encoding="utf-8")).get("raportate", []))


def ore_observate(zi: str) -> list[str]:
    """Orele observate ale zilei, din rezumatul scris de `scenarii_zi`, fără variantele ×0,8 și ×1,2."""
    rez = json.loads((DEMAND_DIR / f"cor_zi_{zi}_rezumat.json").read_text(encoding="utf-8"))
    return [f"cor_zi_{zi}_{f}" for f in rez["ferestre"]]


def sigilata(zi: str) -> bool:
    return ROLURI.get(zi) in ROLURI_SIGILATE or (zi not in ROLURI and zi > max(ROLURI))


def pasi_inainte(zi: str, exclude=()) -> list[Pas]:
    """Până la scenarii: orele observate se află abia din rezumatul lor."""
    return [
        Pas("recount", _m("romana.vision.recount", "--zi", zi, "--camera", "camera_v2.json", "--pe-persoane", "--out", "data/counts_cor"), opreste=True, la_esec="renumărarea a eșuat"),
        Pas("scenarii", _m("romana.bridge.scenarii_zi", "--zi", zi, "--masura", "cor", *[x for e in exclude for x in ("--exclude", e)]), opreste=True, depinde=("recount",), la_esec="scenariile nu s-au generat"),
        Pas("indisciplinat", _m("romana.bridge.indisciplinat", "--scenarii", str(ROOT / "sumo" / "scenarios" / f"cor_zi_{zi}_*.sumocfg"), "--vtypes", "vtypes_indisciplinat_v2.add.xml", "--vechi", "vtypes_v2.add.xml"), depinde=("scenarii",)),
    ]


def pasi_dupa(zi: str, ore: list[str], candidati: list[str], raportate: list[str], desigilat: bool, praguri: Path = PRAGURI) -> list[Pas]:
    """Geamănul față de cameră și, dacă rolul zilei o cere, strategiile și regula."""
    poarta = f"outputs/validare/poarta_cor_{zi}.json"
    fixate = ["--praguri", str(praguri)] if praguri.exists() else []
    lista = [Pas("geaman", _m("romana.control.valideaza_geaman", *ore, "--seeds", SEEDURI_GEAMAN, "--procese", PROCESE_VALIDARE, *fixate, "--poarta", poarta, "--out", f"outputs/validare/geaman_cor_{zi}.csv"), depinde=("scenarii",), iesiri=(poarta,))]
    if sigilata(zi) and not desigilat:
        return lista
    seeduri = SEEDURI_ROL.get(ROLURI.get(zi), SEEDURI_TEST)
    strategii = list(dict.fromkeys([*REFERINTE, *candidati, *raportate]))
    out = {c: f"outputs/validare/cor_test_{zi}_{c}.csv" for c in ("indisciplinat", "normal")}
    for comp, tip, dep in (("indisciplinat", f"indisciplinat_cor_zi_{zi}_*", "indisciplinat"), ("normal", f"cor_zi_{zi}_*", "scenarii")):
        lista.append(Pas(f"test_{comp}", _m("romana.control.validare", *strategii, "--scenarii", tip, "--seeds", seeduri, "--fara-alegere", "--procese", PROCESE_TEST, "--out", out[comp]), depinde=(dep,), iesiri=(out[comp],)))
    if candidati:
        dec = f"outputs/validare/cor_decizie_{zi}.json"
        lista.append(Pas("decizie", _m("romana.control.decizie", *out.values(), "--in-vigoare", *REFERINTE, "--candidati", *candidati, "--poarta", poarta, "--out", dec), depinde=("geaman", "test_indisciplinat", "test_normal"), iesiri=(dec,)))
    return lista


def curata_scenarii(zi: str, note) -> None:
    """`scenarii_zi` nu șterge ce a rămas de la o rulare anterioară, iar tiparele `cor_zi_<zi>_*` le-ar lua din nou."""
    rez = json.loads((DEMAND_DIR / f"cor_zi_{zi}_rezumat.json").read_text(encoding="utf-8"))
    valabile = set(rez["scenarii"])
    dosar = ROOT / "sumo" / "scenarios"
    for cfg in [*dosar.glob(f"cor_zi_{zi}_*.sumocfg"), *dosar.glob(f"indisciplinat_cor_zi_{zi}_*.sumocfg")]:
        if cfg.stem.replace("indisciplinat_", "") not in valabile:
            cfg.unlink()
            note(f"scenariu rămas, șters: {cfg.name}")
    for d in DEMAND_DIR.glob(f"cor_zi_{zi}_*"):
        if d.is_dir() and d.name not in valabile:
            for f in d.iterdir():
                f.unlink()
            d.rmdir()
            note(f"cerere rămasă, ștearsă: {d.name}")


def _sare(p: Pas, cmd: list[str], vechi: dict, refacute: set[str]) -> bool:
    v = vechi.get(p.nume) or {}
    return v.get("cod") == 0 and (v.get("comanda") or [])[1:] == cmd[1:] and not refacute.intersection(p.depinde) and all((ROOT / f).exists() for f in p.iesiri)


def lant(zi: str, exclude=(), reia: bool = False, desigilat: bool = False, rulator=ruleaza) -> int:
    d = DIR_COR / zi
    d.mkdir(parents=True, exist_ok=True)
    note = lambda mesaj: noteaza(d / "jurnal.txt", mesaj)    # noqa: E731
    stare_f = d / "stare.json"
    vechi = json.loads(stare_f.read_text(encoding="utf-8")).get("pasi", {}) if reia and stare_f.exists() else {}
    _, text = prioritate_scazuta()
    note(f"pornit lanțul măsurii noi, ziua {zi}" + (", reluare" if reia else "") + f"; rolul: {ROLURI.get(zi, 'fără rol')}; {text}")
    raw = TRAJ_RAW_DIR / f"traiectorii_{zi}.jsonl.gz"
    if not raw.exists():
        note(f"LIPSEȘTE {raw} – oprire")
        return 1
    stare = {"zi": zi, "pornit": _iso(), "pasi": dict(vechi), "rezultat": "in_curs"}

    def scrie() -> None:
        stare_f.write_text(json.dumps(stare, ensure_ascii=False, indent=1), encoding="utf-8")

    esuate: list[str] = []
    refacute: set[str] = set()

    def ruleaza_pasi(lista: list[Pas]) -> bool:
        for p in lista:
            picate = [x for x in p.depinde if x in esuate]
            if picate:
                note(f"{p.nume}: sărit, depinde de {', '.join(picate)}")
                stare["pasi"][p.nume] = {"cod": None, "sarit": ", ".join(picate)}
                esuate.append(p.nume)
                continue
            if reia and _sare(p, p.comanda, vechi, refacute):
                note(f"{p.nume}: încheiat la {(vechi.get(p.nume) or {}).get('sfarsit')}, sărit")
                continue
            rec = {"cod": None, "inceput": _iso(), "sfarsit": None, "comanda": p.comanda}
            stare["pasi"][p.nume] = rec
            refacute.add(p.nume)
            scrie()
            note("RUN " + " ".join(p.comanda))
            for f in p.iesiri:
                (ROOT / f).unlink(missing_ok=True)
            cod = rulator(p.comanda, d / f"{p.nume}.txt", note)
            rec.update(cod=cod, sfarsit=_iso())
            scrie()
            note(f"   exit {cod}")
            if cod not in p.acceptate:
                esuate.append(p.nume)
                if p.opreste:
                    stare["rezultat"] = f"oprit: {p.la_esec or p.nume}"
                    scrie()
                    note(f"{p.la_esec or p.nume} – oprire")
                    return False
                note(f"{p.nume} a eșuat (cod {cod}); lanțul continuă")
            if p.nume == "scenarii" and cod == 0:
                curata_scenarii(zi, note)
        return True

    if not ruleaza_pasi(pasi_inainte(zi, excluderi_zi(zi, exclude, note))):
        return 1
    if "scenarii" in esuate:
        return 1
    if not ruleaza_pasi(pasi_dupa(zi, ore_observate(zi), lista_candidati(), strategii_raportate(), desigilat)):
        return 1
    stare["rezultat"] = "cu_esecuri: " + ", ".join(esuate) if esuate else ("gata_fara_simulari" if sigilata(zi) and not desigilat else "gata")
    scrie()
    note(f"lanțul măsurii noi, ziua {zi}: {stare['rezultat']}")
    return 1 if esuate else 0


def lant_vechi_incheiat(zi: str) -> bool:
    """Lanțul vechi și-a încheiat ziua, oricum ar fi ieșit: rezultatul nu mai e „în curs”."""
    f = DIR_LANT / zi / "stare.json"
    if not f.exists():
        return False
    try:
        return json.loads(f.read_text(encoding="utf-8")).get("rezultat") != "in_curs"
    except (OSError, ValueError):
        return False


def bucla(ora: str, pana_la: datetime, ceas=datetime.now, dormi=time.sleep, rulare=lant) -> None:
    """În fiecare noapte, la ora dată, ziua de ieri, după lanțul vechi."""
    h, m = map(int, ora.split(":"))
    while True:
        t = ceas()
        urm = t.replace(hour=h, minute=m, second=0, microsecond=0)
        if urm <= t:
            urm += timedelta(days=1)
        if urm > pana_la:
            return
        dormi((urm - t).total_seconds())
        zi = (urm.date() - timedelta(days=1)).isoformat()
        asteptat = 0.0
        while not lant_vechi_incheiat(zi) and asteptat < ASTEPTARE_LANT_VECHI_S:
            dormi(PAS_ASTEPTARE_S)
            asteptat += PAS_ASTEPTARE_S
        try:
            rulare(zi, reia=True)
        except Exception as e:      # o noapte picată nu oprește nopțile următoare
            noteaza(DIR_COR / "bucla.txt", f"{zi}: {e!r}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zi", type=zi_valida)
    ap.add_argument("--exclude", action="append", default=[], metavar="HH:MM-HH:MM")
    ap.add_argument("--reia", action="store_true")
    ap.add_argument("--desigileaza", action="store_true", help="zile de test și de generalizare: rulează și strategiile, după rezultatul validării (§ 9.11)")
    ap.add_argument("--uscat", action="store_true", help="doar arată comenzile")
    ap.add_argument("--bucla", action="store_true")
    ap.add_argument("--ora", default="03:30")
    ap.add_argument("--pana-la", default=None, help="AAAA-LL-ZZ HH:MM")
    a = ap.parse_args(argv)
    if a.bucla:
        bucla(a.ora, datetime.strptime(a.pana_la, "%Y-%m-%d %H:%M"))
        return 0
    zi = a.zi or (date.today() - timedelta(days=1)).isoformat()
    if a.uscat:
        for p in pasi_inainte(zi, uneste([])):
            print(p.nume, " ".join(p.comanda[1:]))
        ore = ore_observate(zi) if (DEMAND_DIR / f"cor_zi_{zi}_rezumat.json").exists() else [f"cor_zi_{zi}_<ora>"]
        for p in pasi_dupa(zi, ore, lista_candidati(), strategii_raportate(), a.desigileaza):
            print(p.nume, " ".join(p.comanda[1:]))
        return 0
    return lant(zi, a.exclude, a.reia, a.desigileaza)


if __name__ == "__main__":
    sys.exit(main())
