"""Teste pentru citirea sigură a jurnalului de traiectorii (`romana.vision.repara`): membri trunchiați sau stricați în
mijlocul fișierului, zone de zerouri, un ultim membru în curs de scriere, antete false sau lungite peste membrii
următori, membri foarte mari, jurnale publicate tăiate, linii fără forma unei traiectorii și copia reparată (date
sintetice, scrise chiar de `od_counter.log_trajectory`).

Rulare:  set PYTHONPATH=src && python -m unittest tests.test_repara
"""
import contextlib
import gzip
import io
import json
import os
import random
import subprocess
import sys
import tempfile
import tracemalloc
import unittest
import zlib
from datetime import datetime
from pathlib import Path
from unittest import mock

from romana.vision import calitate, recount, repara
from romana.vision.calitate import inregistrari, quality
from romana.vision.od_counter import PEDESTRIAN, log_trajectory
from romana.vision.recount import read_trajectories
from romana.vision.repara import citeste_linii, verifica

RADACINA = Path(__file__).resolve().parents[1]
T0 = datetime(2026, 10, 30, 10, 0).timestamp()


def R(membri: int, stricati: int = 0, in_scriere: int = 0, linii: int | None = None) -> dict[str, int]:
    return {"membri": membri, "stricati": stricati, "in_scriere": in_scriere,
            "linii": membri if linii is None else linii}


def scrie_membri(d: Path, trasee: list[list[tuple]]) -> tuple[list[bytes], list[str]]:
    """Membrii scriși chiar de `log_trajectory` (cu numele fișierului în antet și \\r\\n pe Windows) și liniile lor."""
    membri, poz = [], 0
    for i, pts in enumerate(trasee):
        log_trajectory(d, PEDESTRIAN if i == 1 else "passenger", pts)
        date = next(d.glob("*.jsonl.gz")).read_bytes()
        membri.append(date[poz:])
        poz = len(date)
    return membri, [gzip.decompress(m).decode("utf-8").replace("\r\n", "\n") for m in membri]


def jurnal_real(d: Path, n: int = 6) -> tuple[list[bytes], list[str]]:
    """n membri mici, în formatul real."""
    return scrie_membri(d, [[(T0 + i + k * 0.2, round(0.1 + 0.007 * k, 4), round(0.5 + 0.001 * i, 4))
                             for k in range(12 + i)] for i in range(n)])


def stocat(text: bytes) -> bytes:
    """Un membru gzip cu deflate de nivel 0: octeții din `text` apar neschimbați în datele comprimate."""
    return zlib.compress(text, level=0, wbits=31)


def umplutura(lungime: int) -> bytes:
    """Un membru întreg de exact `lungime` octeți (sub 64 KB): antet de 10, bloc stocat, coadă de 8; o linie de text."""
    text = b'"' + b"x" * (lungime - 26) + b'"\n'
    return (b"\x1f\x8b\x08\0\0\0\0\0\x02\xff\x01" + len(text).to_bytes(2, "little")
            + (len(text) ^ 0xFFFF).to_bytes(2, "little") + text
            + zlib.crc32(text).to_bytes(4, "little") + len(text).to_bytes(4, "little"))


class CuJurnal(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.dir = Path(t.name)
        self.membri, self.linii = jurnal_real(self.dir / "scris")
        self.f = self.dir / "jurnal.jsonl.gz"

    def citeste(self, parti: list[bytes]) -> tuple[list[str], dict[str, int]]:
        self.f.write_bytes(b"".join(parti))
        raport = {}
        return list(citeste_linii(self.f, raport)), raport

    def cu_stricat(self, rau: bytes) -> list[bytes]:
        return self.membri[:2] + [rau] + self.membri[3:]

    def verifica_stricat(self, rau: bytes) -> None:
        """Membrul din mijloc înlocuit cu `rau`: restul se citește, iar din el nu ajunge nimic în rezultat."""
        linii, r = self.citeste(self.cu_stricat(rau))
        self.assertEqual(linii, self.linii[:2] + self.linii[3:])
        self.assertEqual(r, R(5, stricati=1))

    def citeste_cu_stderr(self, functie):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            rez = list(functie())
        return rez, err.getvalue()

    def ruleaza(self, *argumente) -> tuple[object, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as c:
            repara.main([str(a) for a in argumente])
        return c.exception.code, out.getvalue(), err.getvalue()


class TestCitire(CuJurnal):
    def test_jurnalul_intreg_se_citeste_ca_prin_gzip(self):
        linii, r = self.citeste(self.membri)
        with gzip.open(self.f, "rt", encoding="utf-8") as fh:
            self.assertEqual(linii, fh.readlines())
        self.assertEqual(linii, self.linii)
        self.assertEqual(r, R(6))
        self.assertEqual(verifica(self.f), R(6))

    def test_un_membru_cu_mai_multe_linii_ca_jurnalul_publicat(self):
        with gzip.open(self.f, "wt", encoding="utf-8") as fh:
            fh.writelines(self.linii)
        r = {}
        self.assertEqual(list(citeste_linii(self.f, r)), self.linii)
        self.assertEqual(r, R(1, linii=6))

    def test_fisier_gol(self):
        self.assertEqual(self.citeste([]), ([], R(0)))

    def test_taiat_la_3_octeti(self):
        self.verifica_stricat(self.membri[2][:3])

    def test_taiat_cu_un_octet_la_coada(self):
        self.verifica_stricat(self.membri[2][:-1])

    def test_taiat_la_jumatate(self):
        self.verifica_stricat(self.membri[2][:len(self.membri[2]) // 2])

    def test_orice_taiere_in_mijloc(self):
        for k in range(1, len(self.membri[2])):
            with self.subTest(octeti=k):
                self.verifica_stricat(self.membri[2][:k])

    def test_orice_taiere_fara_nume_in_antet(self):
        # membri scriși cu gzip.compress: antet de 10 octeți, fără câmpul de nume care ar putea „înghiți” antetul următor
        linii = [f'{{"t0":{i},"tip":"passenger","p":[[0,0.1,0.2],[1,0.3,0.4]]}}\n' for i in range(5)]
        m = [gzip.compress(x.encode(), mtime=1793000000 + i) for i, x in enumerate(linii)]
        for k in range(1, len(m[2])):
            with self.subTest(octeti=k):
                self.assertEqual(self.citeste([*m[:2], m[2][:k], *m[3:]]), (linii[:2] + linii[3:], R(4, stricati=1)))

    def test_octeti_stricati_in_mijloc(self):
        rau = bytearray(self.membri[2])
        rau[len(rau) // 2] ^= 0x55
        rau[len(rau) // 2 + 1] ^= 0xAA
        self.verifica_stricat(bytes(rau))

    def test_crc_gresit(self):
        rau = bytearray(self.membri[2])
        rau[-8] ^= 0xFF                       # primul octet al CRC-ului; datele se decomprimă corect
        self.verifica_stricat(bytes(rau))

    def test_lungime_gresita(self):
        rau = bytearray(self.membri[2])
        rau[-1] ^= 0x01
        self.verifica_stricat(bytes(rau))

    def test_iesirea_unui_membru_cu_crc_gresit_nu_ajunge_in_rezultat(self):
        # deflate de nivel 0: decomprimarea reușește până la capăt și dă text schimbat; doar CRC-ul îl prinde
        rau = bytearray(stocat(self.linii[2].encode()))
        rau[len(rau) // 2] ^= 0x01
        linii, r = self.citeste(self.cu_stricat(bytes(rau)))
        self.assertEqual(linii, self.linii[:2] + self.linii[3:])
        self.assertEqual(r, R(5, stricati=1))

    def test_octeti_stricati_la_intamplare(self):
        rnd = random.Random(20261101)
        for proba in range(200):
            rau = bytearray(self.membri[2])
            for _ in range(rnd.randint(1, 3)):
                rau[rnd.randrange(len(rau))] ^= rnd.randint(1, 255)
            with self.subTest(proba=proba):
                linii, r = self.citeste(self.cu_stricat(bytes(rau)))
                if r["membri"] == 6:          # antetul nu e acoperit de CRC: momentul scrierii sau numele nu strică datele
                    self.assertEqual((linii, r), (self.linii, R(6)))
                else:
                    self.assertEqual((linii, r), (self.linii[:2] + self.linii[3:], R(5, stricati=1)))

    def test_ultimul_membru_incomplet_e_in_scriere(self):
        for k in range(1, len(self.membri[5])):
            with self.subTest(octeti=k):
                linii, r = self.citeste(self.membri[:5] + [self.membri[5][:k]])
                self.assertEqual(linii, self.linii[:5])
                self.assertEqual(r, R(5, in_scriere=1))

    def test_ce_se_adauga_in_timpul_citirii_ramane_pentru_citirea_urmatoare(self):
        self.f.write_bytes(b"".join(self.membri[:3]))
        r = {}
        g = citeste_linii(self.f, r)
        prima = next(g)
        with open(self.f, "ab") as fh:
            fh.write(self.membri[3])
        self.assertEqual([prima, *g], self.linii[:3])
        self.assertEqual(r, R(3))
        self.assertEqual(list(citeste_linii(self.f)), self.linii[:4])


class TestMaiMulteZoneStricate(CuJurnal):
    def test_doi_membri_stricati_la_rand_se_numara_separat(self):
        m = self.membri
        linii, r = self.citeste([m[0], m[1], m[2][:len(m[2]) // 2], m[3][:len(m[3]) // 2], m[4], m[5]])
        self.assertEqual(linii, [self.linii[0], self.linii[1], self.linii[4], self.linii[5]])
        self.assertEqual(r, R(4, stricati=2))

    def test_doua_zone_stricate_separate(self):
        m = self.membri
        linii, r = self.citeste([m[0], m[1][:9], m[2], m[3], m[4][:-3], m[5]])
        self.assertEqual(linii, [self.linii[0], self.linii[2], self.linii[3], self.linii[5]])
        self.assertEqual(r, R(4, stricati=2))

    def test_primul_membru_stricat(self):
        linii, r = self.citeste([self.membri[0][:20], *self.membri[1:]])
        self.assertEqual(linii, self.linii[1:])
        self.assertEqual(r, R(5, stricati=1))

    def test_stricat_si_apoi_in_scriere(self):
        m = self.membri
        linii, r = self.citeste([m[0], m[1], m[2][:40], m[3], m[4], m[5][:30]])
        self.assertEqual(linii, [self.linii[0], self.linii[1], self.linii[3], self.linii[4]])
        self.assertEqual(r, R(4, stricati=1, in_scriere=1))

    def test_ultimii_doi_stricati_si_in_scriere(self):
        m = self.membri
        linii, r = self.citeste([*m[:4], m[4][:len(m[4]) // 2], m[5][:30]])
        self.assertEqual(linii, self.linii[:4])
        self.assertEqual(r, R(4, stricati=1, in_scriere=1))

    def test_octeti_fara_niciun_antet(self):
        gunoi = bytes(random.Random(3).randrange(0x20, 0x7F) for _ in range(300))
        self.verifica_stricat(gunoi)
        linii, r = self.citeste([gunoi, *self.membri])
        self.assertEqual((linii, r), (self.linii, R(6, stricati=1)))
        linii, r = self.citeste([*self.membri, gunoi])
        self.assertEqual((linii, r), (self.linii, R(6, stricati=1)))

    def test_taiat_si_apoi_ultimul_cu_crc_gresit(self):
        # doi membri stricați la capăt, nimic în scriere: o încercare eșuată cu antetul jurnalului nu e o potrivire falsă
        m = self.membri
        rau = bytearray(m[5])
        rau[-8] ^= 0xFF
        for k in range(1, len(m[4])):
            with self.subTest(octeti=k):
                linii, r = self.citeste([*m[:4], m[4][:k], bytes(rau)])
                self.assertEqual((linii, r), (self.linii[:4], R(4, stricati=2)))
        # limita declarată: fără niciun membru întreg nu există un antet de comparat, dar lipsa datelor se anunță
        self.assertEqual(self.citeste([m[4][:3], bytes(rau)]), ([], R(0, in_scriere=1)))
        self.assertIn("niciun membru întreg", self.citeste_cu_stderr(lambda: inregistrari(self.f))[1])

    def test_membru_intreg_in_datele_unui_membru_stricat(self):
        # limita declarată: are CRC-ul lui, deci se citește; la nivelul 9 din jurnal, octeții lui nu apar neschimbați
        inclus = gzip.compress(self.linii[3].encode())
        rau = stocat(b"q" + inclus + b"r" * 50)
        linii, r = self.citeste([self.membri[0], rau[:-10], self.membri[1]])
        self.assertEqual(linii, [self.linii[0], self.linii[3], self.linii[1]])
        self.assertEqual((r["membri"], r["stricati"]), (3, 2))

    def test_fragment_scurt_lipit_de_zona(self):
        # sub 10 octeți, fragmentul nu are XFL și OS ale lui; fără antet întreg (1–2 octeți) nu se numără (limită declarată)
        m = self.membri
        for k in range(1, 10):
            with self.subTest(octeti=k):
                linii, r = self.citeste([m[0], m[1], m[2][:len(m[2]) // 2], m[3][:k], m[4], m[5]])
                self.assertEqual(linii, [self.linii[0], self.linii[1], self.linii[4], self.linii[5]])
                self.assertEqual(r, R(4, stricati=2 if k >= 3 else 1))
                linii, r = self.citeste([*m[:4], m[4][:len(m[4]) // 2], m[5][:k]])
                self.assertEqual(linii, self.linii[:4])
                if k >= 3:
                    self.assertEqual(r, R(4, stricati=1, in_scriere=1))
                else:
                    self.assertEqual((r["membri"], r["stricati"] + r["in_scriere"]), (4, 1))


class TestZerouri(CuJurnal):
    """Zerourile dintre membri nu apar pe jurnalele reale (0 zone în 1 182 721 de membri), dar le poate lăsa o pană de
    curent: sunt o zonă stricată ca oricare alta, nu o umplutură permisă, cum le socotește gzip."""

    Z = b"\0" * 70000                     # peste un bloc de căutare

    def test_o_zona_de_zerouri_se_numara_ca_un_membru_stricat(self):
        m, z = self.membri, self.Z
        for parti, stricati in (([m[0], z, *m[1:]], 1), ([z, *m], 1), ([*m, z], 1), ([m[0], b"\0", *m[1:]], 1),
                                ([*m, b"\0"], 1), ([m[0], z, m[1], z, *m[2:], z], 3)):
            with self.subTest(octeti=sum(map(len, parti))):
                self.assertEqual(self.citeste(parti), (self.linii, R(6, stricati=stricati)))

    def test_membri_inlocuiti_cu_zerouri_nu_se_pierd_in_tacere(self):
        m = self.membri
        for parti, ramase in (([*m[:2], bytes(len(m[2]) + len(m[3])), *m[4:]], (0, 1, 4, 5)),
                              ([*m[:4], bytes(len(m[4]) + len(m[5]))], (0, 1, 2, 3)),
                              ([bytes(len(m[0]) + len(m[1])), *m[2:]], (2, 3, 4, 5))):
            with self.subTest(ramase=ramase):
                linii, r = self.citeste(parti)
                self.assertEqual((linii, r), ([self.linii[i] for i in ramase], R(4, stricati=1)))
                cod, out, _ = self.ruleaza(self.f)
                self.assertEqual(cod, 2)
                self.assertIn("membri=4, stricati=1, in_scriere=0, linii=4", out)

    def test_membru_taiat_urmat_de_zerouri(self):
        # urma tipică a unei pene de curent; la capătul fișierului, zerourile arată că membrul nu mai e în scriere
        m, z = self.membri, b"\0" * 4096
        for k in range(1, len(m[2])):
            with self.subTest(octeti=k):
                intreg = not m[2][k:].strip(b"\0")    # lipseau doar octeții de sus ai lungimii, adică exact zerouri
                linii, r = self.citeste([*m[:2], m[2][:k], z, *m[3:]])
                self.assertEqual(linii, self.linii if intreg else self.linii[:2] + self.linii[3:])
                self.assertEqual(r, R(6 if intreg else 5, stricati=1))
                linii, r = self.citeste([*m[:2], m[2][:k], z])
                self.assertEqual(linii, self.linii[:3 if intreg else 2])
                self.assertEqual(r, R(3 if intreg else 2, stricati=1))

    def test_un_octet_ratacit_la_capat_nu_e_un_membru_in_scriere(self):
        for rau in (b"\0", b"A", b"\x1f\x8b\x07", b"\x1f\x00"):
            with self.subTest(rau=rau):
                self.assertEqual(self.citeste([*self.membri, rau]), (self.linii, R(6, stricati=1)))
        for inceput in (b"\x1f", b"\x1f\x8b", b"\x1f\x8b\x08"):
            with self.subTest(inceput=inceput):
                self.assertEqual(self.citeste([*self.membri, inceput]), (self.linii, R(6, in_scriere=1)))

    def test_copia_reparata_nu_are_zerouri(self):
        dest = self.dir / "copie.jsonl.gz"
        self.f.write_bytes(b"".join([self.membri[0], self.Z, *self.membri[1:], self.Z]))
        self.assertEqual(self.ruleaza(self.f, "--scrie", dest)[0], 2)
        self.assertEqual(dest.read_bytes(), b"".join(self.membri))
        self.assertEqual(self.ruleaza(dest)[0], 0)


class TestAntetFals(CuJurnal):
    # un antet fără valori plauzibile (XFL = 0x55), urmat de un bloc stocat de 65 535 de octeți: zlib nu îl respinge,
    # iar dacă cineva l-ar lua în serios, ar „înghiți” membrii următori și ar rămâne fără date la capătul fișierului
    CAPCANA = b"\x1f\x8b\x08\x00\0\0\0\0\x55\xff" + b"\x00\xff\xff\x00\x00"

    def test_in_datele_unui_membru_intreg(self):
        text = b'{"t0":1}' + self.CAPCANA + b"\r\n"
        linii, r = self.citeste([self.membri[0], stocat(text), self.membri[1]])
        self.assertEqual(linii, [self.linii[0], text.replace(b"\r\n", b"\n").decode("utf-8", "replace"), self.linii[1]])
        self.assertEqual(r, R(3))

    def test_in_datele_unui_membru_stricat_nu_pierde_membrii_urmatori(self):
        rau = stocat(b'{"t0":1}' + self.CAPCANA + b"x" * 200 + b"\n")
        self.verifica_stricat(rau[:len(rau) - 100])

    def test_chiar_la_capatul_unui_membru_stricat(self):
        rau = stocat(b'{"t0":1}' + self.CAPCANA + b"x" * 200 + b"\n")
        self.verifica_stricat(rau[:rau.index(self.CAPCANA) + len(self.CAPCANA)])

    def test_mai_multe_antete_false_in_zona_stricata(self):
        rau = stocat(b"a" + self.CAPCANA * 5 + b"\x1f\x8b\x08\xff" * 5 + b"b" * 300)
        self.verifica_stricat(rau[:len(rau) - 200])

    def test_antet_plauzibil_in_datele_membrului_in_scriere(self):
        # după antetul fals urmează octeți care nu sunt deflate, deci zlib îl respinge: un singur membru, cel în scriere
        fals = gzip.compress(b"nimic\n", mtime=1)[:10]
        rau = stocat(b"a" + fals + b"\xff" * 16 + b"b" * 300)
        linii, r = self.citeste([*self.membri, rau[:len(rau) - 100]])
        self.assertEqual((linii, r), (self.linii, R(6, in_scriere=1)))

    def test_antet_cu_alt_nume_in_datele_membrului_in_scriere(self):
        # FLG, XFL și OS ca ale jurnalului, dar alt nume: tot o potrivire falsă
        antet = self.membri[0][:self.membri[0].index(b"\0", 10) + 1].replace(b"traiectorii", b"alt_jurnal_")
        rau = stocat(b"a" + antet + b"\xff" * 16 + b"b" * 300)
        self.assertEqual(self.citeste([*self.membri, rau[:len(rau) - 100]]), (self.linii, R(6, in_scriere=1)))

    def test_antetul_jurnalului_in_datele_ultimului_membru_nu_e_o_potrivire_falsa(self):
        # o copie exactă a antetului (39 de octeți) nu apare întâmplător: un membru stricat de după unul rămas fără date
        antet = self.membri[0][:self.membri[0].index(b"\0", 10) + 1]
        rau = stocat(b"a" + antet + b"\xff" * 16 + b"b" * 300)
        self.assertEqual(self.citeste([*self.membri, rau[:len(rau) - 100]]), (self.linii, R(6, stricati=2)))

    def test_membru_ramas_fara_date_dar_urmeaza_altii(self):
        # „rămas fără date” la capătul fișierului, dar după el urmează membri întregi: nu era în scriere, ci stricat
        antet = gzip.compress(b"nimic\n", mtime=1)[:10]
        self.verifica_stricat(antet + b"\x00\xff\xff\x00\x00" + b"c" * 10)


class TestAntetLung(CuJurnal):
    """Un antet care sare peste membrii următori: datele de la capătul lui trec de CRC, deci membrul pare întreg, iar
    cei săriți s-ar pierde fără nicio urmă. Capcana cere un membru peste MAX_ANTET (0,24% dintre cei reali): la unul mai
    mic, antetul următor intră în fereastra lui `_inghite_antet`. Fiecare test verifică întâi că zlib chiar cade în ea."""

    def setUp(self):
        super().setUp()
        rnd = random.Random(20261101)
        traseu = [(T0 + k * 0.2, rnd.random(), rnd.random()) for k in range(1200)]
        (self.mare,), _ = scrie_membri(self.dir / "mare", [traseu])
        self.assertGreater(len(self.mare), repara.MAX_ANTET)
        self.assertEqual(self.mare[3], 0x08)

    def test_un_bit_in_flg_nu_pierde_membrii_urmatori(self):
        # FEXTRA: XLEN e „tr” din nume, adică 29 300 de octeți, iar saltul se oprește în numele lui m[2]
        m = self.membri
        nume = m[2].index(b"\0", 10) - 10
        for flg, in_nume in ((0x0C, 0), (0x0C, 5), (0x0C, nume), (0x0D, 5), (0x14, 5), (0x15, 5)):
            with self.subTest(flg=flg, in_nume=in_nume):
                rau = bytearray(self.mare)
                rau[3] = flg
                self.assertEqual(int.from_bytes(rau[10:12], "little"), 29300)
                plin = umplutura(12 + 29300 - len(rau) - 10 - in_nume)
                d = zlib.decompressobj(31)
                self.assertEqual(d.decompress(bytes(rau) + plin + m[2]), gzip.decompress(m[2]))
                self.assertTrue(d.eof)
                linii, r = self.citeste([m[0], m[1], bytes(rau), plin, *m[2:]])
                self.assertEqual(linii, [*self.linii[:2], gzip.decompress(plin).decode(), *self.linii[2:]])
                self.assertEqual(r, R(7, stricati=1))
                self.assertEqual(self.ruleaza(self.f)[0], 2)

    def test_antet_fals_cu_fextra_calculat_nu_sare_peste_membri(self):
        # un membru stricat cu un antet fals, al cărui FEXTRA se oprește chiar la datele unui membru de mai târziu
        m = self.membri
        inceput = b"\x1f\x8b\x08\x08\x55\x66\x77\x88\x02\xffstricat\0\x01"
        coada = b"z" * (repara.MAX_ANTET + 2000)
        for sare in range(1, 5):
            with self.subTest(sare=sare):
                tinta = m[1 + sare]
                xlen = len(coada) + sum(map(len, m[1:1 + sare])) + tinta.index(b"\0", 10) + 1
                fals = b"\x1f\x8b\x08\x04\x11\x22\x33\x44\x02\xff" + xlen.to_bytes(2, "little")
                d = zlib.decompressobj(31)
                self.assertEqual(d.decompress(fals + coada + b"".join(m[1:])), gzip.decompress(tinta))
                self.assertTrue(d.eof)
                linii, r = self.citeste([m[0], inceput + fals + coada, *m[1:]])
                self.assertEqual((linii, r), (self.linii, R(6, stricati=2)))      # două antete plauzibile

    def test_fereastra_antetului(self):
        linie = self.linii[2].encode()
        z = zlib.compressobj(wbits=-15)
        date = (z.compress(linie) + z.flush() + zlib.crc32(linie).to_bytes(4, "little")
                + len(linie).to_bytes(4, "little"))

        def cu_fextra(lungime_antet: int) -> bytes:
            return (b"\x1f\x8b\x08\x04\0\0\0\0\x02\xff" + (lungime_antet - 12).to_bytes(2, "little")
                    + b"e" * (lungime_antet - 12) + date)

        self.assertEqual(gzip.decompress(cu_fextra(repara.MAX_ANTET + 1)), linie)
        self.assertEqual(self.citeste(self.cu_stricat(cu_fextra(40))), (self.linii, R(6)))
        self.assertEqual(self.citeste(self.cu_stricat(cu_fextra(repara.MAX_ANTET))), (self.linii, R(6)))
        self.verifica_stricat(cu_fextra(repara.MAX_ANTET + 1))

    def test_membru_mic_cu_fextra_ramas_fara_date(self):
        rau = bytearray(self.membri[2])
        rau[3] = 0x0C
        self.verifica_stricat(bytes(rau))     # saltul depășește fișierul, dar după el urmează membri întregi
        rau = bytearray(self.membri[5])
        rau[3] = 0x0C                         # limita declarată: ultimul membru nu se deosebește de cel în scriere
        self.assertEqual(self.citeste([*self.membri[:5], bytes(rau)]), (self.linii[:5], R(5, in_scriere=1)))


class TestMembruFoarteMare(CuJurnal):
    """Peste MAX_MEMORIE, membrul se verifică întâi și se citește a doua oară, în flux (praguri mici, fără date mari)."""

    def setUp(self):
        super().setUp()
        rnd = random.Random(11)
        # diacritice, ca un caracter să poată cădea peste granița dintre bucăți; \r\n, ca în jurnalele scrise pe Windows
        self.mare = [json.dumps({"t0": i, "tip": "pietonț", "p": [[rnd.random(), 0.5, 0.5]] * (i % 7)},
                                ensure_ascii=False) + "\n" for i in range(400)]
        self.mare_gz = gzip.compress("".join(self.mare).replace("\n", "\r\n").encode("utf-8"))

    def test_liniile_sunt_aceleasi_la_orice_praguri(self):
        praguri = ((4096, 1 << 20, 64), (7, 13, 64), (1, 1, 10), (4096, 1, 1 << 24), (64, 1 << 20, 1 << 24))
        for bucata, pas, maxim in praguri:
            with self.subTest(bucata=bucata, pas=pas, maxim=maxim), \
                    mock.patch.multiple(repara, BUCATA=bucata, PAS_IESIRE=pas, MAX_MEMORIE=maxim):
                linii, r = self.citeste([self.membri[0], self.mare_gz, self.membri[1]])
                self.assertEqual(linii, [self.linii[0], *self.mare, self.linii[1]])
                self.assertEqual(r, R(3, linii=402))

    def test_membru_foarte_mare_stricat_nu_da_nicio_linie(self):
        rau = bytearray(self.mare_gz)
        rau[-8] ^= 0xFF
        for parte in (bytes(rau), self.mare_gz[:len(self.mare_gz) // 2]):
            with self.subTest(octeti=len(parte)), mock.patch.object(repara, "MAX_MEMORIE", 64):
                self.verifica_stricat(parte)

    def test_membru_foarte_mare_taiat_la_capat_nu_da_nicio_linie(self):
        with mock.patch.object(repara, "MAX_MEMORIE", 64):
            linii, r = self.citeste([*self.membri, self.mare_gz[:-1]])
        self.assertEqual((linii, r), (self.linii, R(6, stricati=1)))

    def test_citirea_e_in_flux(self):
        rnd = random.Random(5)
        parti = [gzip.compress((rnd.randbytes(3000).hex() + "\n").encode(), mtime=1) for _ in range(1000)]
        self.f.write_bytes(b"".join(parti))
        self.assertGreater(self.f.stat().st_size, 3 << 20)
        tracemalloc.start()
        try:
            n = sum(1 for _ in citeste_linii(self.f))
            _, varf = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        self.assertEqual(n, len(parti))
        self.assertLess(varf, 1 << 20)


class TestJurnalPublicatTaiat(CuJurnal):
    """Jurnalul publicat e un singur membru, cu multe linii. Tăiat la capăt (`recount.publish` scrie direct pe
    destinație, o pană de curent poate lăsa o bucată), nu mai e un membru în scriere: nicio linie din el nu ajunge în
    rezultat, cum e regula pentru un membru stricat, dar lipsa lor se anunță. Altfel, ziua întreagă ar dispărea cu
    „[OK] 0 intervale”."""

    def setUp(self):
        super().setUp()
        rnd = random.Random(12)
        linii = [json.dumps({"t0": T0 + i, "tip": "passenger",
                             "p": [[k * 0.2, round(rnd.random(), 4), round(rnd.random(), 4)] for k in range(30)]},
                            separators=(",", ":")) + "\n" for i in range(200)]
        self.date = gzip.compress("".join(linii).encode())

    def test_zero_linii_un_rand_pe_stderr_si_codul_2(self):
        d = self.date
        for parte in (d[:-1], d[:-8], d[:len(d) * 99 // 100], d[:len(d) // 2], d[:2000]):
            with self.subTest(octeti=len(parte)):
                self.f.write_bytes(parte)
                self.assertEqual(verifica(self.f), R(0, stricati=1))
                for functie in (lambda: inregistrari(self.f), lambda: read_trajectories([self.f])):
                    rez, err = self.citeste_cu_stderr(functie)
                    self.assertEqual(rez, [])
                    self.assertEqual(len(err.splitlines()), 1)
                    self.assertIn("membri=0, stricati=1, in_scriere=0, linii=0", err)
                cod, out, _ = self.ruleaza(self.f)
                self.assertEqual(cod, 2)
                self.assertIn("stricati=1", out)

    def test_taiat_dupa_membri_intregi(self):
        self.assertEqual(self.citeste([*self.membri, self.date[:-1]]), (self.linii, R(6, stricati=1)))

    def test_taiat_inainte_de_a_doua_linie_ramane_in_scriere_dar_se_anunta(self):
        # din date nu se poate deosebi de un membru în scriere, însă din fișier nu se citește nimic
        self.f.write_bytes(self.date[:30])
        self.assertEqual(verifica(self.f), R(0, in_scriere=1))
        rez, err = self.citeste_cu_stderr(lambda: inregistrari(self.f))
        self.assertEqual(rez, [])
        self.assertEqual(len(err.splitlines()), 1)
        self.assertIn("niciun membru întreg", err)
        self.assertEqual(self.ruleaza(self.f)[0], 0)

    def test_o_singura_linie_foarte_lunga_ramane_in_scriere(self):
        # mai mare decât cel mai mare membru real (403 082 de octeți comprimați)
        mare = gzip.compress((random.Random(13).randbytes(500_000).hex() + "\r\n").encode())
        self.assertGreater(len(mare), 403_082)
        for parte in (mare[:-1], mare[:-8], mare[:-10], mare[:len(mare) // 2]):
            with self.subTest(octeti=len(parte)):
                self.assertEqual(self.citeste([*self.membri, parte]), (self.linii, R(6, in_scriere=1)))
                self.assertEqual(self.citeste_cu_stderr(lambda: inregistrari(self.f))[1], "")

    def test_comenzile_recount_si_calitate_nu_tac(self):
        gol, pub = self.dir / "gol", self.dir / "pub"
        gol.mkdir()
        pub.mkdir()
        f = pub / "traiectorii_2026-10-30.jsonl.gz"
        f.write_bytes(self.date[:len(self.date) * 99 // 100])
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(recount, "TRAJ_RAW_DIR", gol), mock.patch.object(recount, "TRAJ_DIR", pub), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            recount.main(["--zi", "2026-10-30", "--out", str(self.dir / "numaratori")])
        self.assertIn("[OK] 0 intervale", out.getvalue())
        self.assertEqual(len(err.getvalue().splitlines()), 1)
        self.assertIn("stricati=1", err.getvalue())
        err = io.StringIO()
        with mock.patch.object(sys, "argv", ["calitate", str(f)]), contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(err):
            calitate.main()
        self.assertEqual(len(err.getvalue().splitlines()), 1)
        self.assertIn("stricati=1", err.getvalue())


class TestCititori(CuJurnal):
    """`recount.read_trajectories` și `calitate.inregistrari` citesc prin `citeste_linii`."""

    # JSON valid (sau acceptat de `json.loads`) fără forma scrisă de `log_trajectory`
    FARA_FORMA = ("1", "null", '"text"', "[1,2]", "{}", '{"t0":1.0}', '{"t0":1.0,"tip":"bus"}',
                  '{"tip":"bus","p":[[0,1,2]]}', '{"t0":1.0,"p":[[0,1,2]]}', '{"t0":1.0,"tip":"bus","p":[]}',
                  '{"t0":1.0,"tip":"bus","p":5}',
                  '{"t0":1.0,"tip":"bus","p":{"abc":1}}', '{"t0":1.0,"tip":"bus","p":[[0,1]]}',
                  '{"t0":1.0,"tip":"bus","p":[[0,1,2,3]]}', '{"t0":1.0,"tip":"bus","p":[1,2,3]}',
                  '{"t0":1.0,"tip":"bus","p":["abc"]}', '{"t0":1.0,"tip":"bus","p":[["a",1,2]]}',
                  '{"t0":1.0,"tip":"bus","p":[[0,1,null]]}', '{"t0":"x","tip":"bus","p":[[0,1,2]]}',
                  '{"t0":null,"tip":"bus","p":[[0,1,2]]}', '{"t0":1.0,"tip":7,"p":[[0,1,2]]}',
                  '{"t0":NaN,"tip":"bus","p":[[0,1,2]]}', '{"t0":1.0,"tip":"bus","p":[[Infinity,1,2]]}',
                  '{"t0":1' + "0" * 400 + ',"tip":"bus","p":[[0,1,2]]}', "[" * 200000)

    def asteptate(self, *indici) -> list[dict]:
        return [json.loads(self.linii[i]) for i in indici]

    def test_jurnal_intreg_fara_avertisment_si_ca_citirea_veche(self):
        self.f.write_bytes(b"".join(self.membri))
        vechi = []
        with gzip.open(self.f, "rt", encoding="utf-8") as fh:
            for line in fh:
                vechi.append(json.loads(line))
        rez, err = self.citeste_cu_stderr(lambda: inregistrari(self.f))
        self.assertEqual((rez, err), (vechi, ""))
        rez, err = self.citeste_cu_stderr(lambda: read_trajectories([self.f]))
        tuple_vechi = [(r["t0"], r["tip"], [(r["t0"] + t, x, y) for t, x, y in r["p"]]) for r in vechi]
        self.assertEqual((rez, err), (tuple_vechi, ""))

    def test_membru_stricat_restul_zilei_si_un_singur_rand_de_avertisment(self):
        self.f.write_bytes(b"".join(self.cu_stricat(self.membri[2][:len(self.membri[2]) // 2])))
        for functie in (lambda: inregistrari(self.f), lambda: read_trajectories([self.f])):
            rez, err = self.citeste_cu_stderr(functie)
            self.assertEqual(len(rez), 5)
            self.assertEqual(len(err.splitlines()), 1)
            self.assertIn("membri=5, stricati=1, in_scriere=0, linii=5", err)
            self.assertIn(self.f.name, err)
        self.assertEqual(self.citeste_cu_stderr(lambda: inregistrari(self.f))[0], self.asteptate(0, 1, 3, 4, 5))

    def test_ultimul_membru_in_scriere_nu_avertizeaza(self):
        self.f.write_bytes(b"".join([*self.membri[:5], self.membri[5][:50]]))
        rez, err = self.citeste_cu_stderr(lambda: inregistrari(self.f))
        self.assertEqual((rez, err), (self.asteptate(0, 1, 2, 3, 4), ""))

    def test_linie_json_stricata_nu_pierde_restul(self):
        stricata = '{"t0":1.0,"tip":"passenger","p":[[0,0.1'
        rau = gzip.compress((stricata + "\n").encode())
        linii, r = self.citeste(self.cu_stricat(rau))
        self.assertEqual(linii, [*self.linii[:2], stricata + "\n", *self.linii[3:]])
        self.assertEqual(r, R(6))
        rez, err = self.citeste_cu_stderr(lambda: inregistrari(self.f))
        self.assertEqual(rez, self.asteptate(0, 1, 3, 4, 5))
        self.assertEqual(len(err.splitlines()), 1)
        self.assertIn("linii sărite, fără forma unei traiectorii: 1", err)
        rez, err = self.citeste_cu_stderr(lambda: read_trajectories([self.f]))
        self.assertEqual(len(rez), 5)
        self.assertEqual(len(err.splitlines()), 1)

    def test_linie_json_stricata_intr_un_membru_cu_mai_multe_linii(self):
        rau = gzip.compress(("nu e JSON\n" + self.linii[2]).encode())
        self.f.write_bytes(b"".join(self.cu_stricat(rau)))
        rez, err = self.citeste_cu_stderr(lambda: inregistrari(self.f))
        self.assertEqual(rez, self.asteptate(0, 1, 2, 3, 4, 5))
        self.assertIn("linii sărite, fără forma unei traiectorii: 1", err)
        self.assertEqual(verifica(self.f), R(6, linii=7))

    def test_linie_json_fara_forma_nu_pierde_restul(self):
        for text in self.FARA_FORMA:
            with self.subTest(text=text[:45]):
                self.f.write_bytes(b"".join(self.cu_stricat(gzip.compress((text + "\n").encode()))))
                rez, err = self.citeste_cu_stderr(lambda: read_trajectories([self.f]))
                self.assertEqual([x[0] for x in rez], [r["t0"] for r in self.asteptate(0, 1, 3, 4, 5)])
                self.assertEqual(len(err.splitlines()), 1)
                self.assertIn("linii sărite, fără forma unei traiectorii: 1", err)
                self.assertIn("membri=6, stricati=0, in_scriere=0, linii=6", err)
                rez, err = self.citeste_cu_stderr(lambda: inregistrari(self.f))
                self.assertEqual(rez, self.asteptate(0, 1, 3, 4, 5))
                with contextlib.redirect_stderr(io.StringIO()):
                    per, _ = quality(self.f)
                self.assertEqual(sum(r[4] for r in per.values()), 4)     # membrul 1 e un pieton

    def test_membri_stricati_si_linii_sarite_intr_un_singur_rand(self):
        m = self.membri
        self.f.write_bytes(b"".join([m[0], m[1][:30], gzip.compress(b'{"t0":1.0}\n'), *m[2:]]))
        rez, err = self.citeste_cu_stderr(lambda: inregistrari(self.f))
        self.assertEqual(rez, self.asteptate(0, 2, 3, 4, 5))
        self.assertEqual(len(err.splitlines()), 1)
        self.assertIn("membri stricați săriți", err)
        self.assertIn("linii sărite, fără forma unei traiectorii: 1", err)
        self.assertIn("membri=6, stricati=1, in_scriere=0, linii=6", err)

    def test_un_singur_punct_e_o_traiectorie(self):
        # `log_trajectory` nu cere mai mult; numere întregi, ca după `round`, sunt la fel de bune
        rau = gzip.compress(b'{"t0":1,"tip":"bus","p":[[0,1,0]]}\n')
        self.f.write_bytes(b"".join(self.cu_stricat(rau)))
        rez, err = self.citeste_cu_stderr(lambda: read_trajectories([self.f]))
        self.assertEqual(rez[2], (1, "bus", [(1, 1, 0)]))
        self.assertEqual(err, "")

    def test_mai_multe_fisiere_in_ordine(self):
        a, b = self.dir / "a.gz", self.dir / "b.gz"
        a.write_bytes(self.membri[0] + self.membri[1][:30] + self.membri[2])
        b.write_bytes(b"".join(self.membri[3:]))
        rez, err = self.citeste_cu_stderr(lambda: read_trajectories([a, b]))
        self.assertEqual([x[0] for x in rez], [r["t0"] for r in self.asteptate(0, 2, 3, 4, 5)])
        self.assertEqual(len(err.splitlines()), 1)
        self.assertIn("a.gz", err)


class TestLinieDeComanda(CuJurnal):
    def setUp(self):
        super().setUp()
        self.dest = self.dir / "iesire" / "copie.jsonl.gz"

    def test_cod_0_fara_membri_stricati(self):
        self.f.write_bytes(b"".join(self.membri))
        cod, out, _ = self.ruleaza(self.f)
        self.assertEqual(cod, 0)
        self.assertIn("membri=6, stricati=0, in_scriere=0, linii=6", out)

    def test_cod_0_cu_ultimul_membru_in_scriere(self):
        self.f.write_bytes(b"".join([*self.membri[:5], self.membri[5][:50]]))
        cod, out, _ = self.ruleaza(self.f)
        self.assertEqual(cod, 0)
        self.assertIn("membri=5, stricati=0, in_scriere=1, linii=5", out)

    def test_cod_2_cu_membri_stricati(self):
        self.f.write_bytes(b"".join(self.cu_stricat(self.membri[2][:3])))
        cod, out, _ = self.ruleaza(self.f)
        self.assertEqual(cod, 2)
        self.assertIn("membri=5, stricati=1, in_scriere=0, linii=5", out)

    def test_coduri_prin_proces_separat(self):
        env = dict(os.environ, PYTHONPATH=str(RADACINA / "src"))
        comanda = [sys.executable, "-m", "romana.vision.repara", str(self.f)]
        self.f.write_bytes(b"".join(self.membri))
        self.assertEqual(subprocess.run(comanda, env=env, capture_output=True).returncode, 0)
        self.f.write_bytes(b"".join(self.cu_stricat(self.membri[2][:3])))
        self.assertEqual(subprocess.run(comanda, env=env, capture_output=True).returncode, 2)
        self.assertEqual(subprocess.run(comanda[:3], env=env, capture_output=True).returncode, 1)
        self.assertEqual(subprocess.run([*comanda, "--scrie"], env=env, capture_output=True).returncode, 1)
        self.assertEqual(subprocess.run([*comanda[:3], "--help"], env=env, capture_output=True).returncode, 0)

    def test_eroare_de_utilizare_nu_e_codul_membrilor_stricati(self):
        # `lant_zilnic` și `paznic` iau codul 2 drept „jurnal citibil, cu membri stricați”
        self.f.write_bytes(b"".join(self.membri))
        for argumente in ((), (self.f, "--scrie"), (self.f, "--nu-exista")):
            with self.subTest(argumente=argumente):
                cod, out, err = self.ruleaza(*argumente)
                self.assertEqual(cod, 1)
                self.assertEqual(out, "")
                self.assertIn("eroare", err)

    def test_fisier_inexistent(self):
        cod, _, _ = self.ruleaza(self.dir / "nu_exista.gz")
        self.assertIn("Nu există", str(cod))

    def test_copia_reparata_e_citibila_de_gzip_si_octet_cu_octet(self):
        stricat = self.cu_stricat(self.membri[2][:len(self.membri[2]) // 2])
        self.f.write_bytes(b"".join(stricat))
        cod, out, _ = self.ruleaza(self.f, "--scrie", self.dest)
        self.assertEqual(cod, 2)                                     # codul spune starea sursei
        self.assertIn("stricati=1", out)
        self.assertEqual(self.f.read_bytes(), b"".join(stricat))     # originalul neatins
        self.assertEqual(self.dest.read_bytes(), b"".join(self.membri[:2] + self.membri[3:]))
        with gzip.open(self.dest, "rt", encoding="utf-8") as fh:
            self.assertEqual(fh.readlines(), self.linii[:2] + self.linii[3:])
        self.assertEqual(verifica(self.dest), R(5))
        self.assertEqual(self.ruleaza(self.dest)[0], 0)
        self.assertEqual(sorted(p.name for p in self.dest.parent.iterdir()), [self.dest.name])

    def test_copia_lasa_afara_membrul_in_scriere(self):
        self.f.write_bytes(b"".join([*self.membri, self.membri[0][:50]]))
        cod, _, _ = self.ruleaza(self.f, "--scrie", self.dest)
        self.assertEqual(cod, 0)
        self.assertEqual(self.dest.read_bytes(), b"".join(self.membri))

    def test_copia_scoate_liniile_care_nu_sunt_traiectorii(self):
        for rea in ("nu e JSON\n", '{"t0":1.0,"tip":"bus","p":[[0,1]]}\n'):
            with self.subTest(rea=rea):
                self.dest.unlink(missing_ok=True)
                self.f.write_bytes(b"".join(self.cu_stricat(gzip.compress((rea + self.linii[2]).encode()))))
                cod, out, _ = self.ruleaza(self.f, "--scrie", self.dest)
                self.assertEqual(cod, 0)
                self.assertIn("linii scoase, nu erau traiectorii: 1", out)
                with gzip.open(self.dest, "rt", encoding="utf-8") as fh:
                    self.assertEqual(fh.readlines(), self.linii)
                self.assertEqual(verifica(self.dest), R(6))
                self.assertEqual(self.citeste_cu_stderr(lambda: inregistrari(self.dest))[1], "")

    def test_copia_unui_membru_foarte_mare(self):
        with mock.patch.object(repara, "MAX_MEMORIE", 16):
            self.f.write_bytes(b"".join(self.cu_stricat(self.membri[2][:30])))
            self.assertEqual(self.ruleaza(self.f, "--scrie", self.dest)[0], 2)
            self.assertEqual(self.dest.read_bytes(), b"".join(self.membri[:2] + self.membri[3:]))

    def test_destinatia_nu_poate_fi_sursa(self):
        continut = b"".join(self.cu_stricat(self.membri[2][:30]))
        self.f.write_bytes(continut)
        alta_scriere = self.f.parent / ".." / self.f.parent.name / self.f.name
        for dest in (self.f, alta_scriere):
            cod, _, _ = self.ruleaza(self.f, "--scrie", dest)
            self.assertIn("sursă", str(cod))
            self.assertEqual(self.f.read_bytes(), continut)

    def test_destinatia_existenta_nu_se_suprascrie(self):
        self.f.write_bytes(b"".join(self.membri))
        self.dest.parent.mkdir()
        self.dest.write_bytes(b"alt jurnal")
        cod, _, _ = self.ruleaza(self.f, "--scrie", self.dest)
        self.assertIn("există deja", str(cod))
        self.assertEqual(self.dest.read_bytes(), b"alt jurnal")

    def test_sursa_cu_numele_fisierului_temporar_al_destinatiei(self):
        # numele fișierului temporar nu poate cădea peste sursă, oricum s-ar numi aceasta
        sursa = self.dir / "copie.jsonl.gz.tmp"
        continut = b"".join(self.membri)
        sursa.write_bytes(continut)
        self.assertEqual(self.ruleaza(sursa, "--scrie", self.dir / "copie.jsonl.gz")[0], 0)
        self.assertEqual(sursa.read_bytes(), continut)
        self.assertEqual((self.dir / "copie.jsonl.gz").read_bytes(), continut)


class TestConsolaCalitate(CuJurnal):
    def test_iesirea_redirectionata_fara_utf8(self):
        # cp1250, implicit pe Windows când ieșirea e redirecționată, nu are săgeata din mesajele modulului
        self.f.write_bytes(b"".join(self.membri))
        csv = self.dir / "calitate.csv"
        env = dict(os.environ, PYTHONPATH=str(RADACINA / "src"), PYTHONIOENCODING="cp1250")
        env.pop("PYTHONUTF8", None)
        r = subprocess.run([sys.executable, "-m", "romana.vision.calitate", str(self.f), "--out", str(csv)], env=env,
                           capture_output=True)
        self.assertEqual(r.returncode, 0, r.stderr[-300:])
        self.assertIn("→".encode("utf-8"), r.stdout)
        self.assertTrue(csv.exists())


if __name__ == "__main__":
    unittest.main()
