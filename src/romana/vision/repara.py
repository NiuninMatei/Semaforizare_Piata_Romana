"""Citirea sigură a jurnalului de traiectorii, membru cu membru, și copia reparată a unui jurnal cu membri stricați.

În jurnal, fiecare traiectorie e un membru gzip separat: `od_counter.log_trajectory` deschide fișierul pentru adăugare,
scrie o linie și îl închide. O oprire bruscă poate lăsa în mijlocul zilei un membru trunchiat, iar după repornire se
adaugă alții. Cititorul obișnuit (`gzip.open`) vede toți membrii ca un singur flux și, la cel stricat, pierde restul
zilei: uneori în tăcere (antetul membrului următor e citit drept coada celui trunchiat, iar eroarea e un OSError, luat
până acum drept un ultim bloc incomplet), alteori cu zlib.error.

Aici fiecare membru se decomprimă separat, iar liniile lui ajung în rezultat numai după ce zlib a verificat CRC-ul și
lungimea. După un membru stricat, citirea se reia de la următoarea apariție a antetului gzip. Aceasta poate fi și o
potrivire întâmplătoare în datele comprimate (cam una la 16 milioane de octeți): se încearcă la fel, iar dacă eșuează,
căutarea continuă imediat după ea. Nici un antet stricat, nici unul fals nu trece drept întreg peste membrii de după el:
un antet care cuprinde alt antet sau care depășește MAX_ANTET se socotește stricat (`_inghite_antet`), iar datele care
ar cuprinde alți membri ar trebui să treacă și de CRC, și de lungime. Contoarele din raport:
  * membri     – membrii întregi citiți;
  * stricati   – membrii stricați săriți; o zonă stricată fără niciun antet, de exemplu zerourile pe care le poate lăsa
                 o pană de curent, se numără ca unul singur, oricâți membri ar fi acoperit;
  * in_scriere – 1 dacă fișierul se termină într-un membru incomplet care poate fi cel scris acum, ceea ce e normal cât
                 timp e scris. `log_trajectory` scrie câte o linie, deci o coadă cu mai multe linii (un jurnal publicat,
                 tăiat de o publicare întreruptă) sau terminată în zerouri se numără la `stricati`;
  * linii      – liniile date mai departe, inclusiv cele care nu sunt traiectorii (le sare `citeste_inregistrari`, nu se
                 pierde membrul).

Limitele, cunoscute și declarate; niciuna nu aduce linii greșite:
  * un fragment de 1–2 octeți lipit de o zonă stricată nu se numără, fiindcă nu are un antet întreg; la capătul
    fișierului, fragmentul dinaintea lui trece atunci drept membrul în scriere (stricati=0, in_scriere=1);
  * un ultim membru pe care o stricăciune îl lasă fără date (un bit în FEXTRA, de exemplu) nu se deosebește de cel în
    scriere; la fel, un membru tăiat urmat de unul cu CRC greșit, într-un fișier fără niciun membru întreg (atunci
    `avertizeaza` spune că nu s-a citit nimic);
  * un membru întreg aflat chiar în datele unui membru stricat se citește, fiindcă are CRC-ul lui (jurnalul comprimă la
    nivelul 9, deci octeții unui alt membru nu apar neschimbați în date).

Fișierul se citește în flux și o singură dată (un jurnal are ≈110 MB comprimați, ≈240 000 de membri); doar un membru
foarte mare (jurnalul publicat e unul singur) se decomprimă de două ori: o dată pentru verificare, o dată pentru linii.
Citirea vede fișierul așa cum era la deschidere: ce adaugă între timp colectarea rămâne pentru citirea următoare.

Codurile de ieșire: 0 = fără membri stricați, 2 = cu membri stricați (jurnalul rămâne citibil), 1 = orice eroare,
inclusiv una de utilizare (`lant_zilnic` și `paznic` iau codul 2 drept „membri stricați”).

Exemple:
  python -m romana.vision.repara data/trajectories_brute/traiectorii_2026-10-30.jsonl.gz
  python -m romana.vision.repara data/trajectories_brute/traiectorii_2026-10-30.jsonl.gz --scrie outputs/reparat.gz
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import tempfile
import zlib
from math import isfinite
from pathlib import Path

ANTET = b"\x1f\x8b\x08"        # semnătura gzip și metoda deflate
INCOMPLET, STRICAT = -1, -2    # rezultatul unei încercări nereușite, în locul sfârșitului de membru
AUTENTIC = -3                  # în `_membri`: STRICAT, cu antetul membrilor jurnalului (deci nu o potrivire falsă)
TAMPON = 1 << 18               # octeți; tamponul de citire: întoarcerile la sfârșitul unui membru rămân în el
BUCATA = 1 << 12               # octeți comprimați dați o dată lui zlib (un membru are în medie ≈460)
BLOC = 1 << 16                 # octeți; căutarea antetului și copierea
MAX_ANTET = 1 << 12            # octeți; cel mai lung antet acceptat (în jurnal are 39)
LATIME_ANTET = 12              # octeți; cât cercetează `_pare_membru`: antetul fix și antetul lipit de un fragment
PAS_IESIRE = 1 << 20           # octeți decomprimați, cel mult, dintr-un apel zlib
MAX_MEMORIE = 1 << 24          # octeți decomprimați ținuți în memorie până la verificarea CRC-ului
ZEROURI_COADA = 16             # octeți nuli la capătul fișierului: nu e un membru în scriere (în jurnale, cel mult 4)


def _bucati(f, poz: int, capat: int):
    """Generator: ieșirea decomprimată a membrului de la `poz`, pe bucăți; zlib.error dacă e stricat (zlib verifică și
    antetul, CRC-ul și lungimea). Valoarea de retur: sfârșitul membrului sau INCOMPLET, dacă datele se termină la
    `capat` înaintea lui."""
    d = zlib.decompressobj(31)
    f.seek(poz)
    while poz < capat:
        date = f.read(min(BUCATA, capat - poz))
        if not date:
            break
        poz += len(date)
        while True:
            iesire = d.decompress(date, PAS_IESIRE)
            if iesire:
                yield iesire
            if d.eof:
                return poz - len(d.unused_data)
            date = d.unconsumed_tail
            if not date and len(iesire) < PAS_IESIRE:
                break
    return INCOMPLET


def _incearca(f, poz: int, capat: int) -> tuple[int, bytes | None]:
    """Membrul de la `poz`: (sfârșitul lui, conținutul) sau (INCOMPLET / STRICAT, None). Conținutul unui membru peste
    MAX_MEMORIE nu se păstrează (None): membrul e verificat, iar `_linii_membru` îl decomprimă a doua oară, în flux.
    Un membru rămas fără date e INCOMPLET doar dacă poate fi cel în scriere: `log_trajectory` scrie o singură linie,
    deci unul cu mai multe (un jurnal publicat tăiat) sau cu mai mult de MAX_MEMORIE nu mai așteaptă nimic, e STRICAT."""
    parti, total, g = [], 0, _bucati(f, poz, capat)
    try:
        while True:
            b = next(g)
            total += len(b)
            if total > MAX_MEMORIE:
                parti = None
            else:
                parti.append(b)
    except StopIteration as gata:
        date = None if parti is None else b"".join(parti)
        if gata.value == INCOMPLET:
            return (INCOMPLET if date is not None and b"\n" not in date.rstrip(b"\r\n") else STRICAT), None
        return gata.value, date
    except zlib.error:
        return STRICAT, None


def _pare_membru(a: bytes) -> bool:
    """Primii LATIME_ANTET octeți sunt un antet plauzibil (RFC 1952): fără biți rezervați, XFL 0 / 2 / 4, OS 0–13 sau
    255. O potrivire întâmplătoare a lui ANTET în datele comprimate trece rar, deci nu se numără ca un membru stricat în
    plus. Un fragment sub 10 octeți lipit de membrul următor nu are XFL și OS ale lui: semnul e antetul următor, chiar
    după el."""
    if len(a) > 3 and a[3] & 0xE0:
        return False
    return len(a) < 10 or (a[8] in (0, 2, 4) and (a[9] <= 13 or a[9] == 255)) or ANTET in a[1:]


def _antet(f, poz: int) -> bytes:
    """Primii MAX_ANTET octeți de la `poz`."""
    f.seek(poz)
    return f.read(MAX_ANTET)


def _cheie(a: bytes) -> bytes:
    """Ce au la fel antetele membrilor unui jurnal, adică tot în afară de momentul scrierii: FLG, XFL, OS și numele."""
    return a[3:4] + a[8:(a.find(b"\0", 10) + 1 if a[3:4] == b"\x08" else 10)]


def _inghite_antet(f, poz: int) -> bool:
    """Un antet care sare peste membrii următori: datele de după el trec de CRC, deci membrul pare întreg, iar cei
    săriți se pierd fără urmă. I se întâmplă unui membru trunchiat chiar în antet, al cărui nume cuprinde antetul celui
    următor, și unui singur bit stricat în FLG: cu FEXTRA, „tr” din nume înseamnă un salt de 29 300 de octeți, care se
    poate opri în numele unui membru de mai târziu. Semnele: un alt antet plauzibil în câmpurile antetului (RFC 1952:
    FEXTRA, FNAME, FCOMMENT) sau un antet care depășește MAX_ANTET, cum nu are niciun membru de jurnal."""
    a = _antet(f, poz)
    capat = 10
    if a[3] & 4:
        capat += 2 + int.from_bytes(a[10:12], "little")
    for camp in (8, 16):
        if a[3] & camp:
            i = a.find(b"\0", capat)
            if i < 0:
                return True
            capat = i + 1
    if capat > len(a):
        return True
    i = a.find(ANTET, 1, capat)
    while i >= 0:
        if _pare_membru(a[i:i + LATIME_ANTET]):
            return True
        i = a.find(ANTET, i + 1, capat)
    return False


def _urmatorul_antet(f, poz: int, capat: int) -> int | None:
    """Următoarea apariție a lui ANTET de la `poz` încolo, sau None."""
    while capat - poz >= len(ANTET):
        f.seek(poz)
        bloc = f.read(min(BLOC, capat - poz))
        i = bloc.find(ANTET)
        if i >= 0:
            return poz + i
        if len(bloc) < len(ANTET):
            return None
        poz += len(bloc) - len(ANTET) + 1          # un antet poate cădea peste granița dintre blocuri
    return None


def _membri(f, capat: int, raport: dict[str, int]):
    """Generator: membrii întregi, în ordine, ca (început, sfârșit, conținut; None = prea mare pentru memorie).

    `zona` ține rezultatele încercărilor nereușite de după ultimul membru întreg: prima, oricare ar fi antetul, plus
    cele cu antet plauzibil. Zerourile dintre membri n-au nimic deosebit: pe jurnalele reale nu apar, deci sunt o zonă
    stricată ca oricare alta. Dacă după zonă urmează un membru întreg, toate au fost membri stricați. Dacă zona ajunge
    la capătul fișierului, ultimul membru rămas fără date e cel în curs de scriere (ce eșuează după el e o potrivire
    falsă din datele lui), iar cei dinaintea lui sunt stricați: unul trunchiat, urmat de puțini octeți, poate și el
    rămâne fără date. Nu e în scriere dacă după el a eșuat un membru cu antetul jurnalului, care nu poate fi o potrivire
    falsă (AUTENTIC), sau dacă fișierul se termină în zerouri: atunci toată zona e stricată."""
    poz, zona, intreg = 0, [], None
    while poz < capat:
        sfarsit, date = _incearca(f, poz, capat)
        if sfarsit >= 0 and _inghite_antet(f, poz):
            sfarsit, date = STRICAT, None
        if sfarsit >= 0:
            raport["stricati"] += len(zona)
            zona.clear()
            raport["membri"] += 1
            intreg = poz
            yield poz, sfarsit, date
            poz = sfarsit
            continue
        antet = _antet(f, poz)
        if not ANTET.startswith(antet[:len(ANTET)]):       # zlib nu respinge 1–2 octeți rătăciți la capătul fișierului
            sfarsit = STRICAT
        if not zona or _pare_membru(antet[:LATIME_ANTET]):
            al_jurnalului = sfarsit == STRICAT and intreg is not None and _cheie(antet) == _cheie(_antet(f, intreg))
            zona.append(AUTENTIC if al_jurnalului else sfarsit)
        poz = _urmatorul_antet(f, poz + 1, capat)
        if poz is None:
            break
    if INCOMPLET in zona:
        ultim = len(zona) - 1 - zona[::-1].index(INCOMPLET)
        f.seek(max(capat - ZEROURI_COADA, 0))
        if AUTENTIC not in zona[ultim:] and any(f.read(ZEROURI_COADA)):
            raport["in_scriere"] = 1
            raport["stricati"] += ultim
            return
    raport["stricati"] += len(zona)


def _linii(date: bytes) -> list[str]:
    """Liniile unui text, exact ca în modul text al lui gzip.open: \\r\\n (jurnalul e scris pe Windows) devine \\n."""
    return io.StringIO(date.decode("utf-8", "replace"), newline=None).readlines()


def _linii_membru(f, poz: int, sfarsit: int, date: bytes | None):
    """Liniile unui membru întreg: din conținutul păstrat sau, dacă e foarte mare, decomprimate din nou, în flux."""
    if date is not None:
        yield from _linii(date)
        return
    rest = b""
    for b in _bucati(f, poz, sfarsit):
        rest += b
        i = rest.rfind(b"\n") + 1                  # un \r\n nu se desparte, iar \n nu apare în interiorul unui caracter
        if i:
            yield from _linii(rest[:i])
            rest = rest[i:]
    if rest:
        yield from _linii(rest)


def _raport_nou(raport: dict[str, int] | None = None) -> dict[str, int]:
    raport = {} if raport is None else raport
    raport.update(membri=0, stricati=0, in_scriere=0, linii=0)
    return raport


def citeste_linii(cale, raport: dict[str, int] | None = None):
    """Generator: liniile fiecărui membru întreg, în ordine și în flux; un membru stricat se sare. `raport` (opțional)
    primește contoarele {membri, stricati, in_scriere, linii}, complete la sfârșitul citirii."""
    r = _raport_nou(raport)
    with open(cale, "rb", buffering=TAMPON) as f:
        capat = os.fstat(f.fileno()).st_size
        for poz, sfarsit, date in _membri(f, capat, r):
            for linie in _linii_membru(f, poz, sfarsit, date):
                r["linii"] += 1
                yield linie


def verifica(cale) -> dict[str, int]:
    """Contoarele jurnalului, ca în `citeste_linii`."""
    raport = _raport_nou()
    for _ in citeste_linii(cale, raport):
        pass
    return raport


def _contoare(raport: dict[str, int]) -> str:
    return ", ".join(f"{k}={raport[k]}" for k in ("membri", "stricati", "in_scriere", "linii"))


def avertizeaza(cale, raport: dict[str, int], sarite: int = 0) -> None:
    """Un rând pe stderr dacă din jurnal lipsește ceva: membri stricați (restul zilei s-a citit, dar câteva traiectorii
    lipsesc), niciun membru întreg în fișier, ci doar unul incomplet (s-ar putea să lipsească tot), sau linii sărite."""
    motive = []
    if raport.get("stricati"):
        motive.append("membri stricați săriți")
    elif raport.get("in_scriere") and not raport.get("membri"):
        motive.append("niciun membru întreg")
    if sarite:
        motive.append(f"linii sărite, fără forma unei traiectorii: {sarite}")
    if motive:
        print(f"[jurnal] {Path(cale).name}: {'; '.join(motive)} ({_contoare(raport)})", file=sys.stderr)


def _traiectorie(linie: str) -> dict | None:
    """Traiectoria de pe o linie, sau None dacă linia nu e JSON sau nu are forma scrisă de `log_trajectory`:
    {"t0": număr, "tip": text, "p": [[t, x, y], ...]}, cu cel puțin un punct. Altfel, cititorii s-ar opri în ea."""
    try:
        r = json.loads(linie)
        if not isinstance(r["tip"], str) or not r["p"] or not isfinite(r["t0"]):
            return None
        for t, x, y in r["p"]:
            if not isfinite(t + x + y):
                return None
    except (ValueError, KeyError, TypeError, OverflowError, RecursionError):    # JSONDecodeError e un ValueError
        return None
    return r


def citeste_inregistrari(cale):
    """Generator: traiectoriile din jurnal, pentru `recount` și `calitate`. O linie care nu e o traiectorie (un defect
    al scriitorului; un membru cu CRC corect nu se strică altfel) se sare, fără să se piardă restul zilei; ce lipsește
    se anunță la sfârșit, cu `avertizeaza`."""
    raport, sarite = _raport_nou(), 0
    for linie in citeste_linii(cale, raport):
        r = _traiectorie(linie)
        if r is None:
            sarite += 1
        else:
            yield r
    avertizeaza(cale, raport, sarite)


def scrie_copie(sursa: Path, dest: Path) -> dict[str, int]:
    """Copia reparată: doar membrii întregi, octet cu octet, deci fiecare traiectorie rămâne un membru separat. Un
    membru cu linii care nu sunt traiectorii se comprimă din nou, fără ele. Copia se verifică înainte să primească
    numele `dest`; `sursa` doar se citește. Întoarce contoarele sursei."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=dest.parent, prefix=dest.name + ".")       # un fișier nou, niciodată sursa
    tmp, raport, scoase = Path(tmp), _raport_nou(), 0
    try:
        with os.fdopen(fd, "wb") as g, open(sursa, "rb", buffering=TAMPON) as f:
            for poz, sfarsit, date in _membri(f, os.fstat(f.fileno()).st_size, raport):
                rele = 0
                for linie in _linii_membru(f, poz, sfarsit, date):
                    raport["linii"] += 1
                    rele += _traiectorie(linie) is None
                if rele:
                    z = zlib.compressobj(wbits=31)
                    for linie in _linii_membru(f, poz, sfarsit, date):
                        if _traiectorie(linie) is not None:
                            g.write(z.compress(linie.encode("utf-8")))
                    g.write(z.flush())
                    scoase += rele
                    continue
                f.seek(poz)
                ramas = sfarsit - poz
                while ramas:
                    bloc = f.read(min(BLOC, ramas))
                    if not bloc:
                        raise OSError(f"{sursa} s-a scurtat în timpul copierii")
                    g.write(bloc)
                    ramas -= len(bloc)
        copie, asteptat = verifica(tmp), dict(raport, stricati=0, in_scriere=0, linii=raport["linii"] - scoase)
        if copie != asteptat:
            raise SystemExit(f"Copia nu corespunde: {_contoare(copie)}, așteptat {_contoare(asteptat)}; nu s-a scris.")
        os.replace(tmp, dest)
    finally:
        tmp.unlink(missing_ok=True)
    print(f"[OK] copia reparată: {dest}: {_contoare(asteptat)}"
          + (f"; linii scoase, nu erau traiectorii: {scoase}" if scoase else ""))
    return raport


def main(argv=None) -> None:
    for flux in (sys.stdout, sys.stderr):   # diacriticele merg și când ieșirea e redirecționată fără UTF-8 (cp1250)
        try:
            flux.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.error = lambda mesaj: ap.exit(1, f"{ap.prog}: eroare: {mesaj}\n")      # cu 2 ar părea „membri stricați”
    ap.add_argument("fisier", type=Path, help="jurnalul de traiectorii (doar se citește)")
    ap.add_argument("--scrie", metavar="DESTINATIE", type=Path,
                    help="scrie o copie reparată într-un fișier nou, niciodată peste original")
    a = ap.parse_args(argv)
    if not a.fisier.is_file():
        raise SystemExit(f"Nu există fișierul: {a.fisier}")
    if a.scrie is None:
        raport = verifica(a.fisier)
    else:
        if a.scrie.exists() and os.path.samefile(a.scrie, a.fisier):
            raise SystemExit(f"Destinația e chiar fișierul sursă, care nu se suprascrie: {a.scrie}")
        if a.scrie.exists():
            raise SystemExit(f"Destinația există deja; alegeți alt nume: {a.scrie}")
        raport = scrie_copie(a.fisier, a.scrie)
    print(f"{a.fisier.name}: {_contoare(raport)}")
    sys.exit(2 if raport["stricati"] else 0)


if __name__ == "__main__":
    main()
