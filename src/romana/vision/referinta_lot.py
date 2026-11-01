"""Numărătoarea de referință prin Batch API (§ 4.3): pe foile de contact, ca adnotatorii din 26.10, sau pe felii timp-spațiu, mult mai ieftin.

Fiecare pereche (țintă, bucată) primește doi adnotatori independenți; unde diferă cu mai mult de max(2; 15%), un arbitru le vede
evenimentele și hotărăște. Rezultatul e CSV-ul `tinta,bucata,numar,adnotator` pe care îl citește `referinta factori`. Un lot costă
jumătate din prețul obișnuit, se plătește din creditul Claude Platform și nu încarcă laptopul care colectează. Pe felii (`referinta felii`),
fiecare adnotator vede altă linie, dacă ținta are mai multe, iar fiecare eveniment își spune banda.

Cheia API stă în ~/.anthropic/cheie_semaforizare.txt, în afara depozitului, și ajunge doar la acest proces. Nu se pune în variabila
ANTHROPIC_API_KEY: Claude Code ar trece de pe abonament pe cheie, iar creditul nu îl acoperă. Foile de contact ajung la Anthropic, ca
și la adnotatorii din sesiune, și nu se publică (§ 4.5). Biblioteca `anthropic` stă într-un mediu separat de colectare, outputs/api_venv.

Rulare:  outputs\\api_venv\\Scripts\\python -m romana.vision.referinta_lot trimite --tinte T.json --foi DOSAR --clip NUME --bucati 5,6
         ... aduna LOT --asteapta --out referinta.csv
         ... arbitraj LOT      → lot nou pentru bucățile în care adnotatorii diferă
"""
from __future__ import annotations

import argparse
import base64
import csv
import json
import re
import sys
import time
from pathlib import Path

RADACINA = Path(__file__).resolve().parents[3]
LOTURI = RADACINA / "outputs" / "referinta" / "loturi"
CHEIE = Path.home() / ".anthropic" / "cheie_semaforizare.txt"
MODEL_IMPLICIT = "claude-opus-5-5"
EFORT_IMPLICIT = "max"                # la „high”, adnotatorii gândesc de zece ori mai puțin și pierd vehiculele parțial ascunse (§ 4.3)
EFORTURI = ("low", "medium", "high", "xhigh", "max")
MAX_TOKENI = 120_000                  # gândirea intră în ieșire: pilotul a folosit 41–63 mii de tokeni pe bucată; limita modelului e 128 000
PRET_USD_PE_MILION = {"claude-opus-5-5": (4.0, 20.0), "claude-sonnet-5-5": (2.0, 10.0), "claude-haiku-5-5": (0.10, 0.50)}
REDUCERE_LOT = 0.5
OCTETI_PE_LOT = 200_000_000           # limita API e de 256 MB pe lot
ROLURI = ("Lucrează metodic, imagine cu imagine.",
          "Lucrează independent și sceptic: verifică de două ori fiecare imagine, mai ales vehiculele parțial ascunse.")
SCHEMA = {
    "type": "object",
    "properties": {
        "numar": {"type": "integer"}, "numar_minim": {"type": "integer"}, "numar_maxim": {"type": "integer"},
        "evenimente": {"type": "array", "items": {"type": "object", "properties": {"t": {"type": "number"}, "tip": {"type": "string"}, "descriere": {"type": "string"}},
                                                  "required": ["t", "tip", "descriere"], "additionalProperties": False}},
        "vizibilitate": {"type": "string", "enum": ["buna", "partiala", "proasta"]},
        "observatii": {"type": "string"},
    },
    "required": ["numar", "numar_minim", "numar_maxim", "evenimente", "vizibilitate", "observatii"],
    "additionalProperties": False,
}


def prompt_adnotator(tinta: dict, bucata: int, rol: str, chunk_s: float = 30, conditii: str = "") -> str:
    a, b = bucata * chunk_s, (bucata + 1) * chunk_s
    clip = f"un clip al camerei publice, {conditii}" if conditii else "un clip al camerei publice"
    return "\n".join([
        "Ești adnotator pentru o numărătoare de referință (proiect universitar de trafic, Piața Romană, București).",
        f"Imaginile de mai sus sunt FOI DE CONTACT din {clip}, în ordine. Fiecare foaie are până la 12 imagini, pe 2 coloane, în ORDINEA "
        "TIMPULUI de la stânga la dreapta și de sus în jos, la 0,5 s una de alta; momentul e scris în colț (t = secunde de la începutul clipului). "
        f"Chenar VERDE = imaginea face parte din bucata ta de timp [{a:g}, {b:g}) s; chenar GRI cu „CONTEXT” = 1 s înainte sau după, doar pentru continuitate.",
        f"ȚINTA: {tinta['descriere']}",
        "Regula de numărare: un vehicul (autoturism, taxi, autobuz, troleibuz, camion, motocicletă, bicicletă) se numără o singură dată, în momentul "
        "în care traversează linia roșie în sensul cerut; momentul evenimentului = prima imagine în care e trecut de linie. Numără DOAR evenimentele "
        "al căror moment e într-o imagine cu chenar VERDE. Urmărește fiecare vehicul de la o imagine la alta (culoare, formă, poziție, lumini), ca să "
        "nu-l numeri de două ori și să nu-l pierzi când e acoperit pentru o clipă. La 0,5 s un vehicul se deplasează câțiva metri, deci îl vezi de "
        "obicei în 2–4 imagini consecutive.",
        "În „evenimente” listează fiecare eveniment numărat (t = momentul, tip = tipul vehiculului, descriere scurtă: culoare, bandă, poziție). "
        "„numar” = numărul evenimentelor; „numar_minim” și „numar_maxim” = intervalul tău de încredere (egale cu „numar” dacă ești sigur). "
        "„vizibilitate” = cât de bine se deosebesc vehiculele la linia roșie. În „observatii” spune cinstit, în una-două fraze, ce te-a încurcat și "
        "dacă numărătoarea ți se pare de încredere. Nu numi și nu descrie persoane.",
        rol,
    ])


def rol_arbitru(a: dict, b: dict) -> str:
    return (f"Doi adnotatori au dat {a['numar']} și {b['numar']}. Evenimentele lor: A={json.dumps(a['evenimente'], ensure_ascii=False)} "
            f"B={json.dumps(b['evenimente'], ensure_ascii=False)}. Verifică fiecare eveniment disputat în imagini și dă numărul corect.")


def prompt_arbitru(tinta: dict, bucata: int, a: dict, b: dict, chunk_s: float = 30, conditii: str = "") -> str:
    return prompt_adnotator(tinta, bucata, rol_arbitru(a, b), chunk_s, conditii)


def schema_felie(benzi: list[str]) -> dict:
    """Schema adnotatorilor de felii: în plus față de foi, fiecare eveniment spune banda, ca definiția țintei să poată fi schimbată după numărare."""
    s = json.loads(json.dumps(SCHEMA))
    ev = s["properties"]["evenimente"]["items"]
    ev["properties"]["banda"] = {"type": "string", "enum": list(benzi)}
    ev["required"].append("banda")
    return s


def prompt_felie(tinta: dict, bucata: int, rol: str, chunk_s: float = 30, conditii: str = "", imagini: int = 1) -> str:
    a, b = bucata * chunk_s, (bucata + 1) * chunk_s
    clip = f"un clip al camerei publice, {conditii}" if conditii else "un clip al camerei publice"
    pe_scurt = "Imaginea de mai sus este o FELIE TIMP-SPAȚIU" if imagini == 1 else (
        f"Cele {imagini} imagini de mai sus sunt FELII TIMP-SPAȚIU ale aceluiași trafic, pe linii apropiate, deci un vehicul apare în ele la câteva zecimi de "
        "secundă distanță; fiecare e")
    return "\n".join([
        "Ești adnotator pentru o numărătoare de referință (proiect universitar de trafic, Piața Romană, București).",
        f"{pe_scurt} din {clip}: din fiecare cadru al clipului (18 pe secundă) s-a luat aceeași linie de pixeli, iar liniile s-au pus una lângă alta. "
        "Pe orizontală e TIMPUL, de la stânga la dreapta; fiecare rând al imaginii acoperă 15 s, cu rigla de secunde deasupra (t = secunde de la începutul "
        "clipului). Pe verticală e locul de pe linie. Tot ce stă pe loc apare ca dungi orizontale, iar un vehicul care traversează linia apare ca o singură "
        f"pată, o siluetă de vehicul: cu cât merge mai încet, cu atât e mai lată. Imaginea acoperă exact bucata ta de timp, [{a:g}, {b:g}) s.",
        f"ȚINTA: {tinta['descriere_felie']}",
        "Regula de numărare: un vehicul (autoturism, taxi, autobuz, troleibuz, camion, motocicletă, bicicletă) se numără o singură dată, dacă traversează linia "
        "în sensul cerut. Momentul evenimentului = marginea din stânga a petei, citită pe riglă, adică momentul în care vehiculul ajunge la linie. O pată tăiată "
        "de marginea din stânga a primului rând a început în bucata dinainte și nu se numără. O pată tăiată de capătul unui rând continuă la începutul rândului "
        "următor și se numără o singură dată. Două vehicule care trec în același timp, pe benzi alăturate, apar ca pete suprapuse parțial, una deasupra "
        "celeilalte: deosebește-le după contururi, parbrize și faruri, ca să nu le contopești. Strălucirea farurilor pe asfalt, o pată albă fără contur, nu e "
        "vehicul. Un vehicul care se oprește pe linie apare ca o bandă lată și se numără o singură dată.",
        "În „evenimente” listează, în ordinea timpului, fiecare vehicul numărat (t = momentul, tip = tipul vehiculului, banda, descriere scurtă: culoare, poziție "
        "pe verticală). „numar” = numărul evenimentelor; „numar_minim” și „numar_maxim” = intervalul tău de încredere (egale cu „numar” dacă ești sigur). "
        "„vizibilitate” = cât de bine se deosebesc petele. În „observatii” spune cinstit, în una-două fraze, ce te-a încurcat și dacă numărătoarea ți se pare "
        "de încredere. Nu numi și nu descrie persoane.",
        rol,
    ])


def felii_bucata(dosar: Path, bucata: int) -> list[Path]:
    """Feliile unei bucăți, câte una pe linie, în ordinea liniilor."""
    felii = sorted(dosar.glob(f"b{bucata}_l*.jpg"), key=lambda p: int(p.stem.split("_l")[1]))
    if not felii:
        raise SystemExit(f"Nu există felii pentru bucata {bucata} în {dosar}.")
    return felii


def id_cerere(clip: str, tinta: str, bucata: int, adnotator: str) -> str:
    c = f"{clip}__{tinta}__b{bucata:03d}__{adnotator}"
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", c):
        raise ValueError(f"identificator nepermis de API: {c}")
    return c


def citeste_id(custom_id: str) -> tuple[str, str, int, str]:
    clip, tinta, b, adnotator = custom_id.split("__")
    return clip, tinta, int(b[1:]), adnotator


def foi_bucata(dosar: Path, bucata: int) -> list[Path]:
    foi = sorted(dosar.glob(f"b{bucata}_f*.jpg"), key=lambda p: int(p.stem.split("_f")[1]))
    if not foi:
        raise SystemExit(f"Nu există foi pentru bucata {bucata} în {dosar}.")
    return foi


def cerere(custom_id: str, foi: list[Path], prompt: str, model: str, efort: str, schema: dict = SCHEMA) -> dict:
    continut = [{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.standard_b64encode(f.read_bytes()).decode("ascii")}}
                for f in foi]
    continut.append({"type": "text", "text": prompt})
    return {"custom_id": custom_id,
            "params": {"model": model, "max_tokens": MAX_TOKENI, "output_config": {"effort": efort, "format": {"type": "json_schema", "schema": schema}},
                       "messages": [{"role": "user", "content": continut}]}}


def imparte_pe_loturi(cereri: list[dict], maxim: int = OCTETI_PE_LOT) -> list[list[dict]]:
    """Loturi sub limita de mărime a API-ului, cu toate cererile, în ordine."""
    loturi, curent, marime = [], [], 0
    for c in cereri:
        n = len(json.dumps(c))
        if curent and marime + n > maxim:
            loturi.append(curent)
            curent, marime = [], 0
        curent.append(c)
        marime += n
    if curent:
        loturi.append(curent)
    return loturi


def adnotatori_de_acord(a: float, b: float) -> bool:
    """Aceeași toleranță ca la `referinta.combine_annotators`."""
    return abs(a - b) <= max(2, round(0.15 * max(a, b)))


def cost_usd(model: str, intrare: int, iesire: int) -> float:
    pi, pe = PRET_USD_PE_MILION[model]
    return (intrare * pi + iesire * pe) / 1e6 * REDUCERE_LOT


def scrie_csv(rezultate: dict[str, dict], cale: Path) -> list[dict]:
    """rezultate: identificatorul cererii → {"numar": ...}. Formatul citit de `referinta.load_reference`."""
    randuri = []
    for cid, r in sorted(rezultate.items()):
        _, tinta, bucata, adnotator = citeste_id(cid)
        randuri.append({"tinta": tinta, "bucata": bucata, "numar": r["numar"], "adnotator": adnotator})
    cale.parent.mkdir(parents=True, exist_ok=True)
    with open(cale, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ["tinta", "bucata", "numar", "adnotator"])
        w.writeheader()
        w.writerows(randuri)
    return randuri


def bucati_de_arbitrat(rezultate: dict[str, dict]) -> list[tuple[str, str, int]]:
    """(clip, țintă, bucată) unde doi adnotatori diferă peste toleranță și nu există încă arbitru."""
    pe_bucata: dict[tuple, dict] = {}
    for cid, r in rezultate.items():
        clip, tinta, bucata, adnotator = citeste_id(cid)
        pe_bucata.setdefault((clip, tinta, bucata), {})[adnotator] = r["numar"]
    return sorted(k for k, v in pe_bucata.items() if "0" in v and "1" in v and "arbitru" not in v and not adnotatori_de_acord(v["0"], v["1"]))


def client_api():
    """Cheia ajunge doar aici: din fișier, la acest proces; nu se afișează și nu intră în mediu."""
    import anthropic
    return anthropic.Anthropic(api_key=CHEIE.read_text(encoding="utf-8-sig").strip())


def _salveaza_lot(lot_id: str, meta: dict) -> Path:
    LOTURI.mkdir(parents=True, exist_ok=True)
    cale = LOTURI / f"{lot_id}.json"
    cale.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return cale


def trimite(cereri: list[dict], meta: dict) -> list[str]:
    client = client_api()
    id_uri = []
    for parte in imparte_pe_loturi(cereri):
        lot = client.messages.batches.create(requests=parte)
        _salveaza_lot(lot.id, {**meta, "cereri": [c["custom_id"] for c in parte], "model": parte[0]["params"]["model"]})
        print(f"lot {lot.id}: {len(parte)} cereri, {lot.processing_status}")
        id_uri.append(lot.id)
    return id_uri


def aduna(lot_id: str, asteapta: bool = False) -> dict[str, dict] | None:
    """Rezultatele unui lot; le păstrează lângă metadate, împreună cu consumul și costul."""
    client = client_api()
    meta = json.loads((LOTURI / f"{lot_id}.json").read_text(encoding="utf-8"))
    while True:
        lot = client.messages.batches.retrieve(lot_id)
        if lot.processing_status == "ended":
            break
        print(f"{lot_id}: {lot.processing_status}, în lucru {lot.request_counts.processing}, reușite {lot.request_counts.succeeded}", flush=True)
        if not asteapta:
            return None
        time.sleep(30)
    rezultate, probleme, intrare, iesire = {}, {}, 0, 0
    for r in client.messages.batches.results(lot_id):
        if r.result.type != "succeeded":
            probleme[r.custom_id] = r.result.type
            continue
        m = r.result.message
        intrare += m.usage.input_tokens + (m.usage.cache_creation_input_tokens or 0) + (m.usage.cache_read_input_tokens or 0)
        iesire += m.usage.output_tokens
        if m.stop_reason != "end_turn":
            probleme[r.custom_id] = m.stop_reason
            continue
        rezultate[r.custom_id] = {**json.loads(next(b.text for b in m.content if b.type == "text")), "intrare": m.usage.input_tokens, "iesire": m.usage.output_tokens}
    cost = cost_usd(meta["model"], intrare, iesire)
    _salveaza_lot(lot_id, {**meta, "rezultate": rezultate, "probleme": probleme, "tokeni_intrare": intrare, "tokeni_iesire": iesire, "cost_usd": round(cost, 4)})
    print(f"{lot_id}: {len(rezultate)} rezultate, {len(probleme)} probleme {probleme or ''}; {intrare} tokeni de intrare, {iesire} de ieșire, {cost:.4f} USD")
    return rezultate


def main(argv=None) -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Numărătoarea de referință prin Batch API")
    sub = ap.add_subparsers(dest="comanda", required=True)
    t = sub.add_parser("trimite", help="trimite foile de contact ale unor bucăți, cu doi adnotatori pe fiecare")
    t.add_argument("--tinte", required=True, help="TINTE.json, cu „descriere” pentru fiecare țintă")
    sursa = t.add_mutually_exclusive_group(required=True)
    sursa.add_argument("--foi", help="dosarul cu foi: <foi>/<țintă>/b<k>_f<j>.jpg; ambii adnotatori văd toate foile")
    sursa.add_argument("--felii", help="dosarul cu felii: <felii>/<țintă>/b<k>_l<j>.jpg; fiecare adnotator vede altă linie, dacă sunt mai multe")
    t.add_argument("--toate-liniile", action="store_true", help="la felii, fiecare adnotator vede toate liniile țintei, nu doar una")
    t.add_argument("--clip", required=True)
    t.add_argument("--bucati", required=True, help="de exemplu 5,6")
    t.add_argument("--model", default=MODEL_IMPLICIT, choices=sorted(PRET_USD_PE_MILION))
    t.add_argument("--efort", default=EFORT_IMPLICIT, choices=EFORTURI)
    t.add_argument("--conditii", default="", help="de exemplu „filmat seara, pe întuneric”")
    a = sub.add_parser("aduna", help="rezultatele unui lot")
    a.add_argument("lot")
    a.add_argument("--asteapta", action="store_true", help="așteaptă până se încheie lotul")
    a.add_argument("--out", default=None, help="scrie CSV-ul pentru `referinta factori`")
    r = sub.add_parser("arbitraj", help="un lot cu arbitru pentru bucățile în care adnotatorii diferă")
    r.add_argument("lot")
    r.add_argument("--efort", default=EFORT_IMPLICIT, choices=EFORTURI)
    x = ap.parse_args(argv)
    if x.comanda == "trimite":
        tinte = json.loads(Path(x.tinte).read_text(encoding="utf-8-sig"))
        cereri = []
        for tg in tinte:
            for b in (int(v) for v in x.bucati.split(",")):
                for k, rol in enumerate(ROLURI):
                    cid = id_cerere(x.clip, tg["id"], b, str(k))
                    if x.felii:
                        felii = felii_bucata(Path(x.felii) / tg["id"], b)
                        vazute = felii if x.toate_liniile else [felii[k % len(felii)]]
                        cereri.append(cerere(cid, vazute, prompt_felie(tg, b, rol, conditii=x.conditii, imagini=len(vazute)), x.model, x.efort, schema_felie(tg["benzi"])))
                    else:
                        cereri.append(cerere(cid, foi_bucata(Path(x.foi) / tg["id"], b), prompt_adnotator(tg, b, rol, conditii=x.conditii), x.model, x.efort))
        trimite(cereri, {"clip": x.clip, "mod": "felii" if x.felii else "foi", "dosar": str(x.felii or x.foi), "tinte": x.tinte, "efort": x.efort, "conditii": x.conditii})
    elif x.comanda == "aduna":
        rez = aduna(x.lot, x.asteapta)
        if rez and x.out:
            print("CSV:", Path(x.out), len(scrie_csv(rez, Path(x.out))), "rânduri")
        if rez:
            for cid, v in sorted(rez.items()):
                print(f"  {cid}: {v['numar']} [{v['numar_minim']}–{v['numar_maxim']}], {v['vizibilitate']}")
    else:
        meta = json.loads((LOTURI / f"{x.lot}.json").read_text(encoding="utf-8"))
        tinte = {t["id"]: t for t in json.loads(Path(meta["tinte"]).read_text(encoding="utf-8-sig"))}
        cereri = []
        for clip, tinta, b in bucati_de_arbitrat(meta["rezultate"]):
            ra, rb = (meta["rezultate"][id_cerere(clip, tinta, b, k)] for k in "01")
            cid, dosar = id_cerere(clip, tinta, b, "arbitru"), Path(meta["dosar"]) / tinta
            if meta["mod"] == "felii":
                felii = felii_bucata(dosar, b)
                cereri.append(cerere(cid, felii, prompt_felie(tinte[tinta], b, rol_arbitru(ra, rb), conditii=meta["conditii"], imagini=len(felii)), meta["model"], x.efort, schema_felie(tinte[tinta]["benzi"])))
            else:
                cereri.append(cerere(cid, foi_bucata(dosar, b), prompt_arbitru(tinte[tinta], b, ra, rb, conditii=meta["conditii"]), meta["model"], x.efort))
        print("bucăți de arbitrat:", len(cereri))
        if cereri:
            trimite(cereri, {k: meta[k] for k in ("clip", "mod", "dosar", "tinte", "conditii")} | {"efort": x.efort})


if __name__ == "__main__":
    main()
