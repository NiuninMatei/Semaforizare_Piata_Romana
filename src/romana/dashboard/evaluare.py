"""Evaluarea dispeceratului cu evaluatori AI declarați, prin Batch API (§ 8): găsesc problemele, ele se reunesc, apoi alți evaluatori le verifică.

Evaluatorii văd doar capturile stărilor (`romana.dashboard.capturi`) și codul paginii, nu lista de defecte cunoscute din proiect. Sunt modele de limbaj, nu oameni:
găsesc ce se vede și ce se citește în cod, nu ce simte un utilizator, așa că evaluarea nu înlocuiește sondarea cu oameni (§ 8).

  trimite     5 evaluatori euristici independenți, parcurgerea celor 5 sarcini și auditul de accesibilitate
  reuneste    un lot care reunește problemele găsite într-o singură listă, fără dubluri
  verifica    un lot în care 2 verificatori independenți confirmă sau infirmă fiecare problemă, în capturi și în cod
  rezultat    tabelul final, cu problemele confirmate, CSV în docs/rezultate/evaluare_<versiune>

Cheia și creditul: ca la `romana.vision.referinta_lot`. Rulare din outputs/api_venv:
  python -m romana.dashboard.evaluare trimite --versiune m1
  python -m romana.vision.referinta_lot aduna LOT --asteapta
  python -m romana.dashboard.evaluare reuneste LOT [LOT ...]
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

from romana.vision.referinta_lot import LOTURI, cerere, trimite

RADACINA = Path(__file__).resolve().parents[3]
STATIC = Path(__file__).resolve().parent / "static"
PAGINI = {"m1": STATIC / "m1" / "index.html", "m2": STATIC / "index.html"}
MODEL = "claude-opus-5-5"
EFORT = "xhigh"

CONTEXT = ("„Dispecerat Piața Romană” este interfața unui proiect universitar de licență la disciplina Interfețe om-calculator. O cameră publică numără traficul din Piața Romană, "
           "București, iar un geamăn digital (o simulare SUMO a intersecției) rulează în paralel, cu cererea de trafic măsurată. Dispeceratul arată ce se întâmplă în geamăn și în cameră și "
           "îl lasă pe operator să aleagă cine conduce semaforul din simulare: o strategie automată (un plan fix, un agent antrenat în simulare sau o regulă după cozi) ori comanda manuală. Comenzile ajung doar "
           "la simulare, nu la semafoarele reale. Pagina e în limba română și e folosită de profesor, de colegi și, în sondare, de persoane fără pregătire în trafic.")
EURISTICI = ("1 vizibilitatea stării sistemului; 2 potrivirea cu lumea reală; 3 controlul și libertatea utilizatorului; 4 consecvența și standardele; 5 prevenirea erorilor; "
              "6 recunoaștere, nu reamintire; 7 flexibilitate și eficiență; 8 estetică și minimalism; 9 ajutor la recunoașterea, diagnosticarea și repararea erorilor; 10 ajutor și documentație")
SEVERITATE = ("Severitatea, pe scara lui Nielsen: 0 nu e o problemă; 1 doar cosmetică; 2 minoră; 3 majoră, de reparat cu prioritate; 4 catastrofală, de reparat neapărat înainte de lansare.")
REGULI = ("Reguli: spune doar ce se vede în capturi sau ce se citește în cod, cu dovada: numele capturii sau textul exact de pe ecran, ori fragmentul de cod. Nu inventa comportamente și nu presupune "
          "ce nu poți arăta. Capturile folosesc date simulate, fixate, iar imaginea camerei e o fotografie estompată pusă în locul fluxului; nu raporta valorile sau fotografia în sine. "
          "Scrie în română, scurt și concret; fiecare problemă, o singură dată.")
ROLURI = {
    "E1": "Ești specialist în ergonomia interfețelor. Parcurge pe rând cele 10 euristici, sistematic, pe toate stările.",
    "E2": "Ai lucrat ani la un dispecerat de trafic. Te interesează siguranța lucrului: știi mereu cine conduce semaforul, ce efect are o comandă, dacă a fost aplicată și dacă datele sunt proaspete?",
    "E3": "Nu ai nicio pregătire în trafic, dar folosești calculatorul zilnic. Citești etichetele ad litteram și notezi tot ce nu înțelegi, ce trebuie ghicit și unde nu știi ce să apeși.",
    "E4": "Ești specialist în erori și stări degradate: cameră oprită, simulare oprită, server căzut, comenzi eșuate sau neaplicate. Compară stările între ele: ce rămâne pe ecran și ce crede operatorul?",
    "E5": "Ești specialist în vizualizarea datelor și în limba română: schema intersecției, graficul, tabelul, unitățile, terminologia, coerența numelor, diacriticele și calcurile din engleză.",
}
SARCINI = [
    "Fără să apeși nimic, află cine schimbă acum culorile semaforului: un calculator sau un om.",
    "Află pe care stradă așteaptă acum cele mai multe mașini la semafor.",
    "Dă verde pe Bulevardul Dacia, ca și cum ai schimba tu culorile semaforului, și verifică dacă s-a întâmplat ce ai vrut.",
    "Lasă din nou calculatorul să schimbe singur culorile semaforului.",
    "Află dacă datele de pe ecran sunt la zi și ce trebuie să faci dacă nu sunt.",
]
_PROBLEMA = {"titlu": {"type": "string"}, "descriere": {"type": "string"}, "severitate": {"type": "integer"}, "capturi": {"type": "array", "items": {"type": "string"}},
             "dovada": {"type": "string"}, "recomandare": {"type": "string"}}


def _lista(camp_in_plus: dict, camp_final: str = "ce_merge_bine") -> dict:
    p = {**_PROBLEMA, **camp_in_plus}
    return {"type": "object", "additionalProperties": False, "required": ["probleme", camp_final],
            "properties": {"probleme": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": list(p), "properties": p}},
                           camp_final: {"type": "array", "items": {"type": "string"}}}}


SCHEMA_EURISTICA = _lista({"euristica": {"type": "integer"}})
SCHEMA_PARCURGERE = _lista({"sarcina": {"type": "integer"}, "intrebare": {"type": "string", "enum": ["intentie", "actiune_vizibila", "legatura_actiune_efect", "progres_vizibil"]}}, "sarcini_fara_probleme")
SCHEMA_WCAG = _lista({"criteriu": {"type": "string"}, "nivel": {"type": "string", "enum": ["A", "AA"]}}, "criterii_respectate")
SCHEMA_REUNIRE = {"type": "object", "additionalProperties": False, "required": ["probleme"], "properties": {"probleme": {"type": "array", "items": {
    "type": "object", "additionalProperties": False, "required": ["id", "titlu", "descriere", "severitati", "surse", "capturi", "dovada", "recomandare", "euristici"],
    "properties": {"id": {"type": "string"}, "titlu": {"type": "string"}, "descriere": {"type": "string"}, "severitati": {"type": "array", "items": {"type": "integer"}},
                   "surse": {"type": "array", "items": {"type": "string"}}, "capturi": {"type": "array", "items": {"type": "string"}}, "dovada": {"type": "string"},
                   "recomandare": {"type": "string"}, "euristici": {"type": "array", "items": {"type": "string"}}}}}}}
SCHEMA_VERIFICARE = {"type": "object", "additionalProperties": False, "required": ["verdicte"], "properties": {"verdicte": {"type": "array", "items": {
    "type": "object", "additionalProperties": False, "required": ["id", "verdict", "severitate", "motiv"],
    "properties": {"id": {"type": "string"}, "verdict": {"type": "string", "enum": ["confirmat", "infirmat", "incert"]}, "severitate": {"type": "integer"}, "motiv": {"type": "string"}}}}}}


def capturi(dosar: Path) -> list[Path]:
    fisiere = sorted(dosar.glob("*.jpg"), key=lambda p: (p.stem != "normal", p.stem))
    if not fisiere:
        raise SystemExit(f"Nu există capturi în {dosar}: rulați întâi romana.dashboard.capturi.")
    return fisiere


def _intro(fisiere: list[Path], cod: str) -> str:
    nume = ", ".join(f.stem for f in fisiere)
    return (f"{CONTEXT}\n\nImaginile de mai sus sunt capturi ale paginii, în această ordine: {nume}. Numele spune starea: „normal” e funcționarea obișnuită; telefon_ și tableta_ sunt ecrane mici.\n\n"
            f"Codul paginii:\n<cod>\n{cod}\n</cod>\n\n{REGULI}")


def prompt_euristic(rol: str, fisiere: list[Path], cod: str) -> str:
    return (f"{_intro(fisiere, cod)}\n\nEvaluare euristică, independentă. {rol}\nEuristicile lui Nielsen: {EURISTICI}.\n{SEVERITATE}\n"
            "Listează problemele, de la cea mai gravă, cu numărul euristicii încălcate, și, separat, ce merge bine. Nu raporta probleme de severitate 0.")


def prompt_parcurgere(fisiere: list[Path], cod: str) -> str:
    lista = "\n".join(f"{k}. {s}" for k, s in enumerate(SARCINI, 1))
    return (f"{_intro(fisiere, cod)}\n\nParcurgere cognitivă, pentru o persoană care vede prima dată ecranul și nu știe nimic despre trafic. Sarcinile:\n{lista}\n"
            "Pentru fiecare pas al fiecărei sarcini, răspunde la cele patru întrebări clasice: va încerca persoana să obțină efectul corect (intentie)? Observă că acțiunea corectă e disponibilă "
            "(actiune_vizibila)? Leagă acțiunea de efectul dorit (legatura_actiune_efect)? Vede, după acțiune, că avansează spre scop (progres_vizibil)?\n"
            f"În „probleme” trece doar răspunsurile negative, cu numărul sarcinii și întrebarea. {SEVERITATE} Separat, în „sarcini_fara_probleme”, numește pașii care merg bine.")


def prompt_wcag(fisiere: list[Path], cod: str) -> str:
    return (f"{_intro(fisiere, cod)}\n\nAudit de accesibilitate după WCAG 2.2, nivelurile A și AA. Verifică în cod și în capturi fiecare criteriu aplicabil: alternative text, structură și semantică, "
            "contrastul textului și al elementelor grafice, folosirea culorii ca singur semn, tastatură și focus, ținte de apăsare, redimensionare și reflow, stări anunțate tehnologiilor asistive, nume "
            "accesibile și limba paginii. Dă numărul criteriului (de exemplu 1.4.3) și nivelul; la contrast, dă culorile din cod. "
            f"{SEVERITATE} Separat, în „criterii_respectate”, numește ce e respectat.")


def cereri_evaluare(versiune: str, dosar: Path, model: str = MODEL, efort: str = EFORT) -> list[dict]:
    fisiere = capturi(dosar)
    cod = PAGINI[versiune].read_text(encoding="utf-8")
    out = [cerere(f"{versiune}__{k}", fisiere, prompt_euristic(rol, fisiere, cod), model, efort, SCHEMA_EURISTICA) for k, rol in ROLURI.items()]
    out.append(cerere(f"{versiune}__parcurgere", fisiere, prompt_parcurgere(fisiere, cod), model, efort, SCHEMA_PARCURGERE))
    out.append(cerere(f"{versiune}__wcag", fisiere, prompt_wcag(fisiere, cod), model, efort, SCHEMA_WCAG))
    return out


def rezultate_loturi(loturi: list[str], dosar: Path = LOTURI) -> dict:
    rez = {}
    for lot in loturi:
        m = json.loads((dosar / f"{lot}.json").read_text(encoding="utf-8"))
        if "rezultate" not in m:
            raise SystemExit(f"Lotul {lot} nu are încă rezultate: rulați `referinta_lot aduna`.")
        rez.update(m["rezultate"])
    return rez


def prompt_reunire(gasite: dict) -> str:
    curat = {k.split("__", 1)[1]: v["probleme"] for k, v in gasite.items()}
    return ("Mai mulți evaluatori independenți au evaluat aceeași interfață, „Dispecerat Piața Romană”. Reunește listele lor într-o singură listă, fără dubluri: două intrări care descriu același defect al "
            "aceluiași element devin una, chiar dacă sunt formulate diferit; defecte diferite rămân separate, chiar dacă seamănă. Nu adăuga probleme noi, nu scoate niciuna și nu judeca dacă au dreptate.\n"
            "Pentru fiecare: id scurt (P01, P02, ...), un titlu clar, o descriere care păstrează toate detaliile, severitățile date de fiecare sursă, sursele (cheile listelor), capturile, cea mai bună dovadă, "
            "cea mai bună recomandare și euristicile sau criteriile (de exemplu „N1”, „WCAG 1.4.3”, „sarcina 3”). Ordonează de la cea mai gravă.\n\nListele:\n" + json.dumps(curat, ensure_ascii=False))


def prompt_verificare(probleme: list[dict], fisiere: list[Path], cod: str, rol: str) -> str:
    return (f"{_intro(fisiere, cod)}\n\nAlți evaluatori au raportat problemele de mai jos. Verifică-le independent, una câte una, în capturi și în cod. {rol}\n"
            "Pentru fiecare id: „confirmat” dacă defectul există și îl poți arăta; „infirmat” dacă nu există, dacă dovada e greșită sau dacă ține doar de datele simulate; „incert” dacă nu se poate "
            f"decide din capturi și din cod. Dă și severitatea ta. {SEVERITATE} Motivul, într-o frază, cu dovada.\n\nProblemele:\n" + json.dumps(probleme, ensure_ascii=False))


def grupuri(probleme: list[dict], pe_grup: int = 12) -> list[list[dict]]:
    return [probleme[k:k + pe_grup] for k in range(0, len(probleme), pe_grup)]


def tabel_final(probleme: list[dict], verdicte: list[dict]) -> list[dict]:
    """O problemă e confirmată dacă niciun verificator n-o infirmă și cel puțin unul o confirmă; severitatea e mediana severităților tuturor."""
    pe_id = {}
    for v in verdicte:
        pe_id.setdefault(v["id"], []).append(v)
    out = []
    for p in probleme:
        vs = pe_id.get(p["id"], [])
        conf, inf = sum(v["verdict"] == "confirmat" for v in vs), sum(v["verdict"] == "infirmat" for v in vs)
        sev = [*p["severitati"], *(v["severitate"] for v in vs if v["verdict"] != "infirmat")]
        out.append({"id": p["id"], "titlu": p["titlu"], "severitate": statistics.median(sev) if sev else 0, "confirmat": conf >= 1 and inf == 0, "confirmari": conf, "infirmari": inf,
                    "surse": "; ".join(p["surse"]), "euristici": "; ".join(p["euristici"]), "capturi": "; ".join(p["capturi"]), "descriere": p["descriere"], "dovada": p["dovada"],
                    "recomandare": p["recomandare"], "motive": " | ".join(v["motiv"] for v in vs)})
    return sorted(out, key=lambda r: (not r["confirmat"], -r["severitate"], r["id"]))


def main(argv=None) -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("comanda", choices=("trimite", "reuneste", "verifica", "rezultat"))
    ap.add_argument("loturi", nargs="*", help="loturile cu rezultate: evaluatorii la reuneste, reunirea la verifica, reunirea și verificatorii la rezultat")
    ap.add_argument("--versiune", choices=sorted(PAGINI), default="m1")
    ap.add_argument("--capturi", default=None, help="implicit outputs/evaluare/<versiune>")
    ap.add_argument("--out", default=None, help="implicit docs/rezultate/evaluare_<versiune>")
    ap.add_argument("--doar", default=None, help="la verifica: doar aceste probleme, de exemplu P02,P07, după o corectură a capturilor")
    a = ap.parse_args(argv)
    dosar = Path(a.capturi) if a.capturi else RADACINA / "outputs" / "evaluare" / a.versiune
    if a.comanda == "trimite":
        trimite(cereri_evaluare(a.versiune, dosar), {"mod": "evaluare", "versiune": a.versiune, "efort": EFORT})
    elif a.comanda == "reuneste":
        gasite = rezultate_loturi(a.loturi)
        c = {"custom_id": f"{a.versiune}__reunire", "params": {"model": MODEL, "max_tokens": 120_000, "output_config": {"effort": "high", "format": {"type": "json_schema", "schema": SCHEMA_REUNIRE}},
                                                               "messages": [{"role": "user", "content": [{"type": "text", "text": prompt_reunire(gasite)}]}]}}
        trimite([c], {"mod": "evaluare", "versiune": a.versiune, "efort": "high"})
    elif a.comanda == "verifica":
        probleme = next(iter(rezultate_loturi(a.loturi).values()))["probleme"]
        fisiere, cod = capturi(dosar), PAGINI[a.versiune].read_text(encoding="utf-8")
        roluri = ("Ai experiență în testarea interfețelor.", "Ești sceptic: cauți motive pentru care problema nu există sau e exagerată.")
        eticheta = "verif"
        if a.doar:
            probleme = [p for p in probleme if p["id"] in a.doar.split(",")]
            eticheta = "verif_" + a.doar.replace(",", "_")
        cereri = [cerere(f"{a.versiune}__{eticheta}{g:02d}__{k}", fisiere, prompt_verificare(parte, fisiere, cod, rol), MODEL, EFORT, SCHEMA_VERIFICARE)
                  for g, parte in enumerate(grupuri(probleme)) for k, rol in enumerate(roluri)]
        print(len(probleme), "probleme,", len(cereri), "cereri")
        trimite(cereri, {"mod": "evaluare", "versiune": a.versiune, "efort": EFORT})
    else:
        rez = rezultate_loturi(a.loturi)
        probleme = next(v for k, v in rez.items() if k.endswith("__reunire"))["probleme"]
        verdicte = [x for k, v in rez.items() if "__verif" in k for x in v["verdicte"]]
        randuri = tabel_final(probleme, verdicte)
        out = Path(a.out) if a.out else RADACINA / "docs" / "rezultate" / f"evaluare_{a.versiune}"
        out.mkdir(parents=True, exist_ok=True)
        with open(out / "probleme.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, list(randuri[0]))
            w.writeheader()
            w.writerows(randuri)
        conf = [r for r in randuri if r["confirmat"]]
        print(f"{len(randuri)} probleme, {len(conf)} confirmate; severitate ≥ 3: {sum(r['severitate'] >= 3 for r in conf)} → {out / 'probleme.csv'}")
        for r in conf:
            print(f"  {r['id']} [{r['severitate']:g}] {r['titlu']}")


if __name__ == "__main__":
    main()
