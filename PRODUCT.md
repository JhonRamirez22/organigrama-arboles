# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

delegated: vanilla HTML/CSS/JS sin CDN ni framework, servido por la biblioteca estándar de Python (`http.server`). El usuario delegó la elección ("lo mejor que puedas"). Sin deploy definido: corre en local con `python3 server.py`.

## Users

Primary: personal de RR. HH. y gerencia de una empresa pequeña o mediana. Mantienen la estructura de la empresa: altas, cambios de jefe, bajas y presupuesto por equipo. Usan la app de escritorio durante la jornada de trabajo.

## Product Purpose

Mostrar y mantener el organigrama de una empresa como un árbol navegable. El éxito es que cualquier persona ubique a alguien en la jerarquía en segundos, vea su cadena de mando y su equipo, y pueda ajustar la estructura sin romperla.

## Positioning

Un organigrama donde las preguntas de jerarquía tienen respuesta directa: cadena de mando, ancestro común más cercano entre dos personas ("¿quién aprueba?"), presupuesto de un equipo completo. La estructura es un árbol real, no una lista con jefes asignados.

## Operating Context

Uso de escritorio, en sesiones de consulta y mantenimiento. Los datos actuales son ficticios (`data/organigrama.json`); no hay casos reales ni testimonios.

## Capabilities and Constraints

- Árbol colapsable con búsqueda que resalta coincidencias y expande sus ancestros.
- Panel de detalle: cadena de mando, subordinados directos y totales, presupuesto del equipo, profundidad.
- Altas, edición, movimiento de un equipo completo bajo otro jefe (con prevención de ciclos) y eliminación (los subordinados suben un nivel).
- Herramienta "¿Quién aprueba?": ancestro común más cercano de dos empleados.
- Tabla de presupuesto por área.
- Persistencia en un archivo JSON.
- Sin autenticación, sin multiusuario concurrente. Pendiente de decidir por el usuario.
- Idioma de la interfaz: español.

## Brand Commitments

Ninguno. No hay nombre de marca ni identidad definida.

## Evidence on Hand

Solo datos de ejemplo (15 empleados ficticios). No hay métricas de uso ni casos de cliente. No inventar testimonios ni cifras.

## Product Principles

- La jerarquía se lee de un vistazo: el árbol es el objeto principal y todo lo demás lo apoya.
- Cada acción de modificación tiene que ser reversible en la práctica o pedir confirmación cuando destruye datos.
- Los errores de estructura (ciclos, duplicados, borrar un director con equipo) se explican en lenguaje claro, no con códigos.

## Accessibility & Inclusion

Pendiente de definir con el usuario. Mínimo razonable: navegación por teclado en el árbol, contraste de texto AA y etiquetas en todos los campos.
