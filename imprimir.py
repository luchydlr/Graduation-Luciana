#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convierte menu/index.html en un PDF listo para imprimir y para subir a Canva.

    python3 build.py && python3 imprimir.py

Sale menu/menu-cena.pdf, una tarjeta de 10 x 21 cm. Las letras van dentro del
PDF (no son una foto), así que Canva las abre como texto editable.
"""
import base64
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.request import Request, urlopen

FUENTE = "menu/index.html"
SALIDA = "menu/menu-cena.pdf"
CACHE = ".fuentes"          # las tipografías bajadas, para no repetir la descarga

# Google Fonts mira quién pregunta para decidir el formato. A un navegador
# viejo, como este, le manda .ttf sueltos: son los que Chrome sabe meter en el
# PDF como letra de verdad.
NAVEGADOR = "Mozilla/5.0 (X11; Linux x86_64)"

# Google Fonts sirve tipografías variables, y Chrome las mete en el PDF como
# dibujos (Type 3): imprimen bien, pero Canva ya no las abre como texto. Esta
# otra dirección devuelve versiones fijas, que sí viajan como letra de verdad.
CSS_ESTATICO = ("https://fonts.googleapis.com/css?family="
                "Bodoni+Moda:400,400i,500|IBM+Plex+Mono:400,500|Jost:300,400,500")

CROMOS = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
          "chrome", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]


def baja(url):
    """Baja una URL una sola vez y la guarda en .fuentes/."""
    os.makedirs(CACHE, exist_ok=True)
    guardado = os.path.join(CACHE, re.sub(r"[^\w.-]", "_", url)[-120:])
    if os.path.exists(guardado):
        return io.open(guardado, "rb").read()
    datos = urlopen(Request(url, headers={"User-Agent": NAVEGADOR}), timeout=60).read()
    io.open(guardado, "wb").write(datos)
    return datos


def incrustar(html):
    """Cambia el <link> de Google Fonts por las letras metidas en el HTML.

    Chrome imprime sin red, y así el PDF lleva las tipografías de verdad.
    """
    enlace = re.search(r'<link rel="stylesheet" href="(https://fonts\.googleapis[^"]+)">', html)
    if not enlace:
        return html
    css = baja(CSS_ESTATICO).decode("utf-8")
    for url in sorted(set(re.findall(r"url\((https://fonts\.gstatic\.com[^)]+)\)", css))):
        b64 = base64.b64encode(baja(url)).decode("ascii")
        css = css.replace(url, "data:font/woff2;base64," + b64)
    html = re.sub(r'<link rel="preconnect"[^>]*>\n?', "", html)
    return html.replace(enlace.group(0), "<style>\n%s\n</style>" % css)


def cromo():
    for nombre in CROMOS:
        camino = shutil.which(nombre) or (nombre if os.path.exists(nombre) else None)
        if camino:
            return camino
    # El navegador que trae Playwright, si está instalado.
    for raiz in ("/opt/pw-browsers", os.path.expanduser("~/.cache/ms-playwright")):
        for sub in sorted(os.listdir(raiz) if os.path.isdir(raiz) else [], reverse=True):
            camino = os.path.join(raiz, sub, "chrome-linux", "chrome")
            if os.path.exists(camino):
                return camino
    sys.exit("No encontré Chrome ni Chromium. Instálalo o exporta CHROME=/ruta/al/chrome")


def imprimir():
    html = incrustar(io.open(FUENTE, encoding="utf-8").read())
    temporal = os.path.join(tempfile.mkdtemp(), "menu.html")
    io.open(temporal, "w", encoding="utf-8").write(html)

    salida = os.path.abspath(SALIDA)
    subprocess.run([os.environ.get("CHROME") or cromo(),
                    "--headless", "--disable-gpu", "--no-sandbox",
                    "--no-pdf-header-footer", "--virtual-time-budget=4000",
                    "--print-to-pdf=" + salida, temporal],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("escrito", SALIDA, os.path.getsize(salida) // 1024, "KB")


if __name__ == "__main__":
    imprimir()
