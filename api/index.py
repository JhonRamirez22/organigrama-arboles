"""Entrada serverless de Vercel para la API del organigrama.

Vercel no permite escribir en el código desplegado, salvo en /tmp. La primera vez
que arranca una instancia copiamos los datos de ejemplo a /tmp y la API trabaja
sobre esa copia. Los cambios duran mientras la instancia viva; al reciclarse,
la copia vuelve a los datos de ejemplo.
"""

import os
import shutil
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

DATOS_SEMILLA = os.path.join(RAIZ, "data", "organigrama.json")
DATOS_TEMPORALES = "/tmp/organigrama.json"

if not os.path.exists(DATOS_TEMPORALES):
    shutil.copyfile(DATOS_SEMILLA, DATOS_TEMPORALES)
os.environ["ORG_DATA_FILE"] = DATOS_TEMPORALES

# Debe importarse después de fijar ORG_DATA_FILE: server.py carga los datos al importarse.
from server import Manejador  # noqa: E402


class handler(Manejador):
    """Clase que Vercel busca al ejecutar la función."""
