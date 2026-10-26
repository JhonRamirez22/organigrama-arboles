# Design

Surface: organigrama de empresa (Operate). Ver [PRODUCT.md](PRODUCT.md).

## Scene

Una persona de RR. HH. o gerencia, a media tarde, con un portátil junto a una hoja de cálculo bajo luz de oficina. Necesita ubicar a alguien en la jerarquía en segundos y ajustar la estructura sin romperla. Por eso: fondo claro y neutro, texto denso pero legible, nada que compita con el árbol.

## Color

Estrategia: **Restrained**. Neutros con un ligero tinte frío y un solo acento.

| Token | Valor | Uso |
|---|---|---|
| `--ink-shell` | `#18212f` | Barra superior |
| `--ground` | `#f2f4f7` | Fondo de la página |
| `--surface` | `#ffffff` | Paneles |
| `--ink` | `#18212f` | Texto principal (≈ 15:1 sobre blanco) |
| `--ink-2` | `#4b5565` | Texto secundario (≈ 7:1 sobre blanco) |
| `--line` | `#d8dde6` | Bordes y separadores |
| `--accent` | `#0f6e6a` | Selección, enlaces, botón principal (≈ 6:1 con blanco) |
| `--accent-tint` | `#e2f0ef` | Cadena de mando, fondos de hover |
| `--approve` | `#b7791f` | Contorno del ancestro común ("¿Quién aprueba?") |
| `--approve-tint` | `#fbf1dc` | Fondo del ancestro común |
| `--danger` | `#b42318` | Solo acciones destructivas |

Color con trabajo real: el acento marca la selección y la cadena de mando; el ámbar marca quién aprueba; el rojo aparece solo en "Eliminar".

## Tipografía

Fuente del sistema (`system-ui`, `-apple-system`, `Segoe UI`). Es una herramienta de trabajo: la jerarquía viene del peso y del tamaño, no de una cara de display.

- Base 14px, filas del árbol 14px, encabezados 15px (600) y el nombre del panel de detalle 20px (600).
- Cifras de salario y tablas con `font-variant-numeric: tabular-nums`.
- Interlineado 1.45. Sin tracking negativo.

## Forma y densidad

- Densidad compacta: filas del árbol de 32px.
- Radios: 12px en paneles, 8px en controles.
- Elevación: solo borde. Sin sombras.
- Márgenes: 16px de gutter en móvil, 24px entre columnas en escritorio.

## Firma

**La cadena de mando dentro del árbol.** Al seleccionar a una persona, todos sus jefes hasta la dirección general se pintan con el tinte de acento. Así se ve de un vistazo de dónde viene cada persona. El ancestro común de "¿Quién aprueba?" se marca en ámbar en el mismo árbol.

Las conexiones entre niveles son líneas verticales finas (1px, `--line`), sin ornamento.

## Movimiento

Ninguno, salvo un cambio de fondo de 120ms en hover. Respeta `prefers-reduced-motion`.

## Estados

- Foco: contorno de 2px en `--accent` con offset de 2px, visible en todos los controles.
- Hover: fondo `--accent-tint`.
- Deshabilitado: opacidad 0.5 y cursor por defecto.
- Vacío: "No hay empleados todavía." y "Sin resultados" en la búsqueda.
- Error: notificación con fondo `--danger` y el mensaje del servidor en lenguaje claro.

## Accesibilidad

- Cada fila del árbol es un botón con nombre accesible; el chevron de expandir tiene `aria-expanded` y etiqueta.
- Contraste de todo el texto ≥ 4.5:1.
- Todos los campos tienen etiqueta visible.

## Lo que no hacemos

Sin degradados, sin vidrio, sin iconos Unicode como sustituto de un sistema de iconos (el chevron está dibujado con bordes), sin texto de acento sobre fondo de acento, sin tarjetas dentro de tarjetas, sin etiquetas pequeñas encima de los títulos.
