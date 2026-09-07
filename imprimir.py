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
ANCHO, ALTO = 378, 794      # la tarjeta en píxeles de pantalla: 10 x 21 cm
ESCALA = 3                  # x3 para que el fondo salga a unos 300 puntos por pulgada
VENTANA = (500, 900)        # la ventana con la que se fotografía el fondo
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


def medir(navegador, molde, ancho, alto):
    """Pregunta al navegador cuánto mide la tarjeta y cuánto ve de la página."""
    sonda = ("<script>addEventListener('load',function(){"
             "var r=document.querySelector('.card').getBoundingClientRect();"
             "document.body.setAttribute('data-caja',[r.width,r.height,innerWidth,innerHeight]"
             ".join(','));});</script>")
    io.open(molde, "a", encoding="utf-8").write(sonda)
    dom = subprocess.run([navegador, "--headless", "--disable-gpu", "--no-sandbox",
                          "--hide-scrollbars", "--force-device-scale-factor=%d" % ESCALA,
                          "--window-size=%d,%d" % (ancho, alto),
                          "--virtual-time-budget=4000", "--dump-dom", molde],
                         capture_output=True, text=True).stdout
    medidas = re.search(r'data-caja="([\d.,]+)"', dom)
    if not medidas:
        sys.exit("No pude medir la tarjeta: ¿cambió menu/index.html?")
    return [float(n) for n in medidas.group(1).split(",")]


def fondo(navegador, pagina):
    """Devuelve el degradé de la tarjeta como una imagen, en una regla de CSS.

    Canva no entiende los degradés que Chrome escribe en el PDF: los repinta a
    escalones y en otro color. Una foto del fondo, en cambio, la respeta. Se
    fotografía la propia página con el contenido escondido, para que la imagen
    salga siempre del mismo CSS y no haya dos fondos que mantener.
    """
    # La tarjeta se pega a la esquina y se le esconde el contenido: así la foto
    # empieza justo donde empieza la tarjeta.
    escondido = ("<style>body{ display: block !important }"
                 " .card{ margin: 0 !important }"
                 " .card > *{ visibility: hidden }</style>")
    molde = os.path.join(tempfile.mkdtemp(), "fondo.html")
    io.open(molde, "w", encoding="utf-8").write(pagina + escondido)

    # Chrome no abre ventanas de menos de 500 de ancho y se come unos 90 de
    # alto, así que se pide una ventana con holgura y se comprueba que la
    # tarjeta quepa entera; si no, se estira lo que falte.
    ancho, alto = VENTANA
    tarjeta_ancho, tarjeta_alto, _, visible = medir(navegador, molde, ancho, alto)
    if visible < tarjeta_alto:
        alto += int(tarjeta_alto - visible) + 4

    png = os.path.join(os.path.dirname(molde), "fondo.png")
    subprocess.run([navegador, "--headless", "--disable-gpu", "--no-sandbox",
                    "--hide-scrollbars", "--force-device-scale-factor=%d" % ESCALA,
                    "--window-size=%d,%d" % (ancho, alto),
                    "--virtual-time-budget=4000", "--screenshot=" + png, molde],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # La foto es más grande que la tarjeta: se estira en la misma proporción
    # para que su esquina de arriba a la izquierda calce, y lo que sobra cae
    # fuera de la tarjeta.
    b64 = base64.b64encode(io.open(png, "rb").read()).decode("ascii")
    return ("<style>\n  .card{ background: url(data:image/png;base64,%s)"
            " 0 0 / %.3f%% %.3f%% no-repeat, var(--plate) !important; }\n</style>"
            % (b64, ancho / tarjeta_ancho * 100, alto / tarjeta_alto * 100))


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
    navegador = os.environ.get("CHROME") or cromo()
    html = incrustar(io.open(FUENTE, encoding="utf-8").read())
    html += fondo(navegador, html)
    temporal = os.path.join(tempfile.mkdtemp(), "menu.html")
    io.open(temporal, "w", encoding="utf-8").write(html)

    salida = os.path.abspath(SALIDA)
    subprocess.run([navegador,
                    "--headless", "--disable-gpu", "--no-sandbox",
                    "--no-pdf-header-footer", "--virtual-time-budget=4000",
                    "--print-to-pdf=" + salida, temporal],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("escrito", SALIDA, os.path.getsize(salida) // 1024, "KB")


if __name__ == "__main__":
    imprimir()
