# Organigrama: árboles en Python con frontend

Aplicación para gestionar el organigrama de una empresa. La estructura de datos central es un **árbol N-ario**: cada empleado es un nodo, el director general es la raíz y cada persona tiene un jefe y una lista de subordinados.

Caso de estudio: RR. HH. y gerencia necesitan saber quién reporta a quién, quién aprueba un asunto que involucra a dos personas y cuánto cuesta cada equipo. Esas preguntas son operaciones directas sobre un árbol.

## Requisitos

- Python 3.10 o superior.
- Ninguna dependencia externa: solo biblioteca estándar.

## Ejecutar

```bash
python3 server.py
```

Abrir <http://localhost:8000>. Para otro puerto: `python3 server.py 5000`.

## Pruebas

```bash
python3 -m unittest discover -s tests -v
```

## Despliegue en Vercel

Demo en vivo: <https://organigrama-arboles.vercel.app>

- `api/index.py` es la función serverless que reutiliza `server.py`.
- `public/` contiene la interfaz; `vercel.json` enruta `/api/*` a la función.
- **Limitación de persistencia:** Vercel no permite escribir en el código desplegado. La función trabaja sobre una copia en `/tmp` que se crea desde `data/organigrama.json`. Los cambios duran mientras la instancia esté activa y se pierden al reciclarse. Para datos permanentes hace falta una base de datos externa (por ejemplo Postgres o Vercel KV).

## Operaciones del árbol

| Operación | Método | Complejidad |
|---|---|---|
| Buscar un empleado por id | `get` (índice `dict`) | O(1) |
| Agregar bajo un jefe | `add` | O(1) |
| Mover un equipo completo | `move` (valida ciclos recorriendo hacia arriba) | O(h) |
| Eliminar (reportes suben un nivel) | `remove` | O(k), k = reportes directos |
| Cadena de mando | `chain_of_command` | O(h) |
| Ancestro común más cercano (LCA) | `lowest_common_ancestor` | O(h) |
| Subordinados (todo el subárbol) | `reports_of` (DFS iterativo) | O(n) |
| Presupuesto de un equipo | `team_budget` (postorden) | O(n) |
| Presupuesto por área | `budget_by_area` (BFS) | O(n) |
| Búsqueda por texto | `search` (BFS) | O(n) |
| Altura y profundidad | `height`, `depth` | O(n), O(h) |

n = empleados, h = altura del árbol, k = reportes directos de un empleado.

## Estructura

```
organigrama/
  __init__.py      exporta Employee y OrgChart
  org_chart.py     clases Employee (nodo) y OrgChart (árbol y sus operaciones)
server.py          API HTTP y archivos estáticos (solo biblioteca estándar)
api/
  index.py         entrada serverless para Vercel (reutiliza server.py)
public/
  index.html       interfaz
  style.css        estilos
  app.js           lógica del frontend (sin frameworks)
data/
  organigrama.json datos de ejemplo (ficticios); el servidor lo guarda al modificar
tests/
  test_org_chart.py pruebas de las operaciones del árbol
DESIGN.md          decisiones visuales
PRODUCT.md         contexto de producto
```

## API

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/organigrama` | Árbol anidado y estadísticas |
| GET | `/api/empleados/<id>` | Detalle, cadena de mando y subordinados |
| POST | `/api/empleados` | Alta (`id`, `nombre`, `cargo`, `area`, `salario`, `jefe_id`) |
| PUT | `/api/empleados/<id>` | Edición de datos |
| POST | `/api/empleados/<id>/mover` | Mover equipo bajo otro jefe (`jefe_id`) |
| DELETE | `/api/empleados/<id>` | Baja |
| GET | `/api/buscar?q=` | Búsqueda por nombre, cargo o área |
| GET | `/api/comun?a=&b=` | Ancestro común más cercano |

Los errores devuelven `400` (validación) o `404` (no existe), con `{"error": "..."}`.

## Decisiones de diseño

- **Índice + árbol:** `OrgChart` guarda un diccionario `id -> Employee` para llegar a un nodo en O(1). La jerarquía vive en los punteros `manager` y `reports`; el índice no cambia la forma del árbol.
- **Sin ciclos:** `move` rechaza mover a alguien bajo una persona de su propio equipo.
- **La raíz no se mueve ni se elimina con equipo:** evita dejar el organigrama sin director.
- **Frontend sin dependencias:** el diseño está en `DESIGN.md`. La cadena de mando de la persona seleccionada se resalta dentro del propio árbol.
