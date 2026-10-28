#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Revisar posibles enlaces votacion-expediente (Congreso, legislatura XV).

Version resistente a errores de conexion; nunca modifica la web publica.
Se ejecuta desde scripts/ dentro de la carpeta del proyecto v0.8.

Prueba corta (red):
  py scripts\\proponer_expedientes_v08_revisado.py --fecha 2024-11-28

Modo local, tras guardar un HTML desde el navegador con nombre YYYY-MM-DD.html:
  py scripts\\proponer_expedientes_v08_revisado.py --html-dir sesiones --fecha 2024-11-28

Procesar varias sesiones en red, con parada ante errores repetidos:
  py scripts\\proponer_expedientes_v08_revisado.py --limite-sesiones 10

Los resultados son PROPUESTAS, no enlaces comprobados para publicacion.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote

ROOT = Path(__file__).resolve().parent.parent
SOURCE = "https://www.congreso.es/es/opendata/votaciones"
R_EXP = re.compile(r"\b(\d{3}/\d{6})\b")
R_VOTE = re.compile(r"Sesion0*(\d+)/\d{8}/Votacion0*(\d+)/[^\s\"?#]+\.json", re.I)
FIELDS = ["votacion_id", "fecha", "url_sesion", "expediente_candidato", "url_votacion", "metodo"]


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.events = []
        self.ignored = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.ignored += 1
        if tag == "a" and not self.ignored:
            href = dict(attrs).get("href", "")
            if R_VOTE.search(href):
                self.events.append(("json", urljoin(SOURCE, href)))

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.ignored:
            self.ignored -= 1

    def handle_data(self, text):
        if not self.ignored:
            t = " ".join(text.split())
            if t:
                self.events.append(("txt", t))


def last_number(block, pattern):
    matches = re.findall(pattern, block, re.I)
    return int(matches[-1]) if matches else None


def parse_html(text):
    parser = PageParser()
    parser.feed(text)
    exp = ""
    texts_since_vote = []
    text_context = []
    rows = []
    for kind, value in parser.events:
        if kind == "txt":
            texts_since_vote.append(value)
            text_context.append(value)
            text_context = text_context[-25:]
            context = " ".join(text_context)
            # Capturar el expediente explicitamente impreso en el listado.
            if re.search(r"(?:n[uú]m\.?\s*)?exp(?:te\.?|ediente)", context, re.I):
                matches = R_EXP.findall(context)
                if matches:
                    exp = matches[-1]
            continue
        match = R_VOTE.search(value)
        if not match:
            continue
        # El HTML puede dividir Si: y la cifra en elementos distintos.
        block = " ".join(texts_since_vote)
        rows.append({
            "sesion": str(int(match.group(1))),
            "numero": str(int(match.group(2))),
            "url_votacion": value,
            "expediente": exp,
            "si": last_number(block, r"\bS[ií]\s*:\s*(\d+)"),
            "no": last_number(block, r"\bNo\s*:\s*(\d+)"),
            "abstencion": last_number(block, r"\bAbstenciones?\s*:\s*(\d+)"),
        })
        texts_since_vote.clear()
    return rows


def official_date_url(date):
    return SOURCE + "?targetLegislatura=XV&targetDate=" + date[8:10] + "%2F" + date[5:7] + "%2F" + date[:4]


def canonical_url(url):
    p = urlsplit(url)
    # Las URL de cada JSON incluyen una marca de tiempo; esta SI debe coincidir.
    return (p.netloc.lower(), unquote(p.path).lower())


def http_get(url, timeout, retries, pause):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Connection": "close",
    }
    error = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as response:
                content = response.read(8_000_000)
            return content.decode("utf-8", errors="replace")
        except (urllib.error.HTTPError, urllib.error.URLError, ConnectionError, socket.timeout, TimeoutError, OSError) as exc:
            error = exc
            if isinstance(exc, urllib.error.HTTPError) and exc.code in (401, 403, 404, 429):
                # No eludir restricciones del servidor.
                break
            if attempt < retries:
                print(f"  Conexion fallida ({type(exc).__name__}: {exc}). Reintento {attempt+1}/{retries}...", flush=True)
                time.sleep(min(20, pause * (2 ** attempt)))
    raise RuntimeError(str(error))


def load_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=";"))


def save_proposals(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter=";", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fecha", help="Una fecha YYYY-MM-DD; ideal para probar")
    parser.add_argument("--desde", default="")
    parser.add_argument("--hasta", default="")
    parser.add_argument("--html-dir", type=Path, help="Carpeta de paginas guardadas como YYYY-MM-DD.html")
    parser.add_argument("--limite-sesiones", type=int, default=0, help="Maximo de fechas intentadas (por defecto todas salvo errores repetidos)")
    parser.add_argument("--errores-max", type=int, default=3, help="Parar tras N errores consecutivos en red")
    parser.add_argument("--reintentos", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=12)
    parser.add_argument("--pausa", type=float, default=2.0)
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "descargas" / "sesiones_html")
    parser.add_argument("--out", type=Path, default=ROOT / "datos" / "expedientes_propuestos_v08.csv")
    parser.add_argument("--informe", type=Path, default=ROOT / "datos" / "informe_recuperacion_v08.json")
    args = parser.parse_args()
    if args.fecha:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.fecha):
            parser.error("La fecha debe tener el formato YYYY-MM-DD")
        args.desde = args.hasta = args.fecha
    if args.html_dir and not args.html_dir.is_absolute():
        args.html_dir = Path.cwd() / args.html_dir
    if not args.cache_dir.is_absolute():
        args.cache_dir = Path.cwd() / args.cache_dir
    if args.reintentos < 0 or args.errores_max < 1:
        parser.error("Reintentos debe ser >= 0; errores-max debe ser >= 1")
    reference_file = ROOT / "datos" / "votaciones_referencia_XV.csv"
    link_file = ROOT / "datos" / "vinculos_XV.csv"
    if not reference_file.exists() or not link_file.exists():
        parser.error("No encuentro los CSV de la v0.8. Copia este archivo dentro de la carpeta scripts del proyecto original.")
    reference = {r["id"]: r for r in load_csv(reference_file)}
    sessions = defaultdict(list)
    for record in load_csv(link_file):
        if record["votacion_id"].startswith("s203-ll") or record["expediente_id"]:
            continue
        parsed = re.fullmatch(r"s(\d+)-v\d+", record["votacion_id"])
        if not parsed:
            parsed = R_VOTE.search(record["url_votacion"])
        if not parsed:
            continue
        session = str(int(parsed.group(1)))
        sessions[(session, record["fecha"])].append(record)
    all_rows = []
    matched_votes = set()
    # Conservar propuestas guardadas en ejecuciones anteriores del mismo proyecto.
    if args.out.exists():
        with args.out.open("r", encoding="utf-8-sig", newline="") as saved:
            for old in csv.DictReader(saved, delimiter=";"):
                if old.get("votacion_id") in reference and old.get("votacion_id") not in matched_votes:
                    all_rows.append({field: old.get(field, "") for field in FIELDS})
                    matched_votes.add(old["votacion_id"])
        print(f"Propuestas previas conservadas: {len(all_rows)}", flush=True)
    errors = []
    processed = 0
    consecutive = 0
    checked = []
    for (session, date), records in sorted(sessions.items(), key=lambda item: (item[0][1], int(item[0][0]))):
        if args.desde and date < args.desde or args.hasta and date > args.hasta:
            continue
        if args.limite_sesiones and processed >= args.limite_sesiones:
            break
        processed += 1
        print(f"[{processed}] Fecha {date}, sesion {session}", flush=True)
        local_page = (args.html_dir / (date + ".html")) if args.html_dir else args.cache_dir / (date + ".html")
        if local_page.exists():
            html = local_page.read_text(encoding="utf-8", errors="replace")
            origin = "archivo local"
        elif args.html_dir:
            errors.append({"fecha": date, "error": "No existe " + str(local_page)})
            print("  No existe el HTML; se omite.", flush=True)
            continue
        else:
            try:
                html = http_get(official_date_url(date), args.timeout, args.reintentos, args.pausa)
                args.cache_dir.mkdir(parents=True, exist_ok=True)
                local_page.write_text(html, encoding="utf-8")
                origin = "descarga"
                time.sleep(args.pausa)
            except Exception as exc:
                consecutive += 1
                errors.append({"fecha": date, "error": str(exc)[:250]})
                print(f"  ERROR descarga {date}: {exc}", flush=True)
                if consecutive >= args.errores_max:
                    print("  PARADA SEGURA: demasiados errores consecutivos. Prueba el modo --html-dir.", flush=True)
                    break
                continue
        candidates = parse_html(html)
        if not candidates:
            errors.append({"fecha": date, "error": "HTML sin enlaces JSON de votacion (portal cambiado, pagina de error o documento incompleto)"})
            print("  HTML sin enlaces JSON reconocidos. No se publicara ninguna coincidencia.", flush=True)
            if not args.html_dir:
                consecutive += 1
                if consecutive >= args.errores_max:
                    print("  PARADA SEGURA: varias paginas no validas.", flush=True)
                    break
            continue
        consecutive = 0
        by_url = {canonical_url(item["url_votacion"]): item for item in candidates}
        before = len(all_rows)
        for record in records:
            expected = reference.get(record["votacion_id"])
            found = by_url.get(canonical_url(record["url_votacion"]))
            if not expected or not found or not found["expediente"]:
                continue
            try:
                if any(found[field] is None or found[field] != int(expected[field]) for field in ("si", "no", "abstencion")):
                    continue
            except (ValueError, TypeError):
                continue
            if record["votacion_id"] in matched_votes:
                continue
            matched_votes.add(record["votacion_id"])
            all_rows.append({
                "votacion_id": record["votacion_id"],
                "fecha": date,
                "url_sesion": official_date_url(date),
                "expediente_candidato": found["expediente"],
                "url_votacion": record["url_votacion"],
                "metodo": "URL JSON y cifras coincidentes; expediente impreso en HTML; REVISION HUMANA PENDIENTE",
            })
        print(f"  {origin}: {len(candidates)} JSON; {len(all_rows)-before} expedientes propuestos", flush=True)
        checked.append(date)
        save_proposals(args.out, all_rows)  # Guarda el avance despues de cada fecha.
    save_proposals(args.out, all_rows)
    args.informe.parent.mkdir(parents=True, exist_ok=True)
    args.informe.write_text(json.dumps({
        "fechas_intentadas": processed,
        "fechas_con_html_valido": len(checked),
        "coincidencias": len(all_rows),
        "errores": errors,
        "aviso": "PROPUESTAS PENDIENTES DE REVISION; NUNCA ALTERAR LA WEB PUBLICADA AUTOMATICAMENTE",
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nFinalizado: {len(all_rows)} candidatos. CSV: {args.out}", flush=True)
    print(f"Informe: {args.informe}", flush=True)
    if errors and not checked:
        print("No se pudo leer ninguna sesion. Comprobar pagina en navegador y usar --html-dir.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario. No se modifico la web publicada.", flush=True)
        sys.exit(130)
