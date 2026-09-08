# Graduación Luciana

Páginas de participación, invitación y menú para el grado de Ingeniería
Electrónica de Luciana De la Rosa Padilla — Universidad del Norte, 25 de
septiembre de 2026.

- `index.html` — **la participación**: fecha, hora, lugar y el aviso de la
  transmisión en vivo para quien no pueda ir en persona.
- `cena/index.html` — **la invitación a la cena**: Rincón del Viejo Country,
  8:00 p. m., invita Milena Padilla. Confirma por WhatsApp y el número de
  cupos sale del enlace (`?pases=2`).
- `menu/index.html` — **el menú impreso** de la cena: tarjeta de 10 x 21 cm,
  una por puesto.
- `cena.html` — solo redirige a `cena/`, por los enlaces ya repartidos.
- Las dos primeras llevan la sección **En memoria** del papá y el abuelo.

## Cómo se editan

Nada se escribe a mano en los HTML: todos salen de `build.py`.

    python3 build.py        # genera index.html, cena/, menu/ y cena.html

- Los datos de cada página están arriba, en `PAGINAS` y en `MENU_DATOS`.
- El diseño está en `SHELL` (las tarjetas) y en `MENU` (el impreso).
- La paleta (`COLORES`) y las tipografías (`FUENTES`) se escriben una sola vez
  y las usan las dos plantillas, para que todo se vea de la misma familia.

## El menú para imprimir

    python3 build.py && python3 imprimir.py     # escribe menu/menu-cena.pdf

Sale un PDF de una página de 10 x 21 cm, con las letras incrustadas como texto
de verdad: se puede subir a Canva (Subir → Archivos → abrir como diseño) y
editar los platos ahí mismo. Al imprimir, pedir cartulina mate y decirle al
taller que **no** ajuste al tamaño de la hoja.

Pendiente, marcado en el HTML con la clase `pending`: el enlace de la
transmisión.
