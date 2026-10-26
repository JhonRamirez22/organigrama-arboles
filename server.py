"""Servidor HTTP con la API del organigrama y el frontend estático.

Sin dependencias externas: usa solo la biblioteca estándar de Python.

    python3 server.py            # http://localhost:8000
    python3 server.py 5000       # otro puerto
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, unquote, urlparse

from organigrama import OrgChart

RAIZ = os.path.dirname(os.path.abspath(__file__))
CARPETA_STATIC = os.path.join(RAIZ, "public")
ARCHIVO_DATOS = os.environ.get("ORG_DATA_FILE", os.path.join(RAIZ, "data", "organigrama.json"))

TIPOS = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
}

chart = OrgChart.load(ARCHIVO_DATOS) if os.path.exists(ARCHIVO_DATOS) else OrgChart()


def guardar():
    chart.save(ARCHIVO_DATOS)


def detalle_empleado(id):
    nodo = chart.get(id)
    return {
        **nodo.to_dict(),
        "jefe_id": nodo.manager.id if nodo.manager else None,
        "profundidad": chart.depth(id),
        "cadena": [e.to_dict() for e in chart.chain_of_command(id)],
        "subordinados": [e.to_dict() for e in chart.reports_of(id)],
        "presupuesto_equipo": chart.team_budget(id),
    }


def datos_empleado(cuerpo, completo=True):
    """Valida y convierte el JSON recibido en argumentos para el árbol."""
    campos = {}
    for clave in ("nombre", "cargo", "area"):
        if clave in cuerpo:
            campos[clave] = str(cuerpo[clave] or "")
    if "salario" in cuerpo:
        campos["salario"] = float(cuerpo["salario"])
    if completo:
        campos.setdefault("nombre", "")
        campos.setdefault("cargo", "")
        campos.setdefault("area", "")
        campos.setdefault("salario", 0.0)
    return campos


# Los campos del JSON se mantienen en español; los atributos de Python, en inglés.
MAPA_CAMPOS = {"nombre": "name", "cargo": "role", "area": "area", "salario": "salary"}


class Manejador(BaseHTTPRequestHandler):

    def do_GET(self):
        ruta = urlparse(self.path)
        if ruta.path.startswith("/api/"):
            return self.responder_api("GET", ruta)
        return self.servir_archivo(ruta.path)

    def do_POST(self):
        self.responder_api("POST", urlparse(self.path))

    def do_PUT(self):
        self.responder_api("PUT", urlparse(self.path))

    def do_DELETE(self):
        self.responder_api("DELETE", urlparse(self.path))

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------

    def responder_api(self, metodo, ruta):
        partes = [unquote(p) for p in ruta.path.strip("/").split("/")]
        consulta = {k: v[0] for k, v in parse_qs(ruta.query).items()}
        try:
            estado, cuerpo = self.despachar(metodo, partes, consulta)
        except KeyError as error:
            estado, cuerpo = 404, {"error": str(error.args[0])}
        except ValueError as error:
            estado, cuerpo = 400, {"error": str(error)}
        except json.JSONDecodeError:
            estado, cuerpo = 400, {"error": "El cuerpo de la petición no es JSON válido"}
        self.enviar_json(estado, cuerpo)

    def despachar(self, metodo, partes, consulta):
        # partes[0] es "api"
        recurso = partes[1] if len(partes) > 1 else ""

        if recurso == "organigrama" and metodo == "GET":
            return 200, {"arbol": chart.to_dict(), "estadisticas": chart.stats()}

        if recurso == "buscar" and metodo == "GET":
            resultados = chart.search(consulta.get("q", ""))
            return 200, [e.to_dict() for e in resultados]

        if recurso == "comun" and metodo == "GET":
            ancestro = chart.lowest_common_ancestor(consulta.get("a", ""), consulta.get("b", ""))
            return 200, {"ancestro": ancestro.to_dict() if ancestro else None}

        if recurso == "empleados":
            if len(partes) == 2 and metodo == "POST":
                cuerpo = self.leer_cuerpo()
                datos = datos_empleado(cuerpo)
                chart.add(
                    cuerpo["id"],
                    datos["nombre"],
                    datos["cargo"],
                    datos["area"],
                    datos["salario"],
                    cuerpo.get("jefe_id") or None,
                )
                guardar()
                return 201, detalle_empleado(cuerpo["id"])

            id = partes[2] if len(partes) > 2 else None
            accion = partes[3] if len(partes) > 3 else None

            if id and accion is None and metodo == "GET":
                return 200, detalle_empleado(id)

            if id and accion is None and metodo == "PUT":
                datos = datos_empleado(self.leer_cuerpo(), completo=False)
                chart.update(id, **{MAPA_CAMPOS[k]: v for k, v in datos.items()})
                guardar()
                return 200, detalle_empleado(id)

            if id and accion is None and metodo == "DELETE":
                chart.remove(id)
                guardar()
                return 200, {"eliminado": id}

            if id and accion == "mover" and metodo == "POST":
                cuerpo = self.leer_cuerpo()
                chart.move(id, cuerpo.get("jefe_id"))
                guardar()
                return 200, detalle_empleado(id)

        return 404, {"error": "Ruta no encontrada"}

    def leer_cuerpo(self):
        longitud = int(self.headers.get("Content-Length", 0) or 0)
        if longitud == 0:
            return {}
        return json.loads(self.rfile.read(longitud).decode("utf-8"))

    def enviar_json(self, estado, cuerpo):
        datos = json.dumps(cuerpo, ensure_ascii=False).encode("utf-8")
        self.send_response(estado)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    # ------------------------------------------------------------------
    # Archivos estáticos
    # ------------------------------------------------------------------

    def servir_archivo(self, ruta):
        if ruta in ("", "/"):
            ruta = "/index.html"
        ruta_archivo = os.path.normpath(os.path.join(CARPETA_STATIC, unquote(ruta).lstrip("/")))
        if not ruta_archivo.startswith(CARPETA_STATIC + os.sep) or not os.path.isfile(ruta_archivo):
            self.send_error(404)
            return
        extension = os.path.splitext(ruta_archivo)[1]
        with open(ruta_archivo, "rb") as archivo:
            contenido = archivo.read()
        self.send_response(200)
        self.send_header("Content-Type", TIPOS.get(extension, "application/octet-stream"))
        self.send_header("Content-Length", str(len(contenido)))
        self.end_headers()
        self.wfile.write(contenido)

    def log_message(self, formato, *args):
        pass  # sin ruido en la consola por cada petición


def main():
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    servidor = HTTPServer(("127.0.0.1", puerto), Manejador)
    print(f"Organigrama disponible en http://localhost:{puerto}  (Ctrl+C para salir)")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")


if __name__ == "__main__":
    main()
