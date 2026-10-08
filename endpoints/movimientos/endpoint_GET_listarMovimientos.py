# endpoint_GET_listarMovimientos.py
# GET /api/movimientos
#
# Lista los movimientos ordenados por idMovimiento (ASC).
# Se usa LIMIT para no traer toda la tabla de una sola vez.

import json
import os
import sys

# Para poder ejecutar este archivo con el boton Run de VS Code:
# se agrega la carpeta raiz del proyecto a la ruta de Python.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from db_connection import ejecutar_consulta, ErrorBaseDatos

LIMITE_POR_DEFECTO = 50


def listar_movimientos(limite=LIMITE_POR_DEFECTO, desde=0):
    """Devuelve una lista de diccionarios (vacia si no hay movimientos)."""
    sql = """
        SELECT
            idMovimiento,
            idCuenta,
            tipo,
            monto,
            fechaMovimiento,
            descripcion,
            idMeta,
            idCategoria,
            idCuentaDestino
        FROM movimientos
        ORDER BY idMovimiento ASC
        LIMIT %s OFFSET %s
    """
    return ejecutar_consulta(sql, (limite, desde))


def ejecutar_GET():
    """Entrada del script."""
    try:
        movimientos = listar_movimientos()
        print(json.dumps(movimientos, indent=2, ensure_ascii=False, default=str))
    except ErrorBaseDatos as error_bd:
        print("Error de base de datos: " + error_bd.mensaje)
    except Exception as error_inesperado:
        print("Error inesperado. Contacte al administrador. Detalle: " + str(error_inesperado))


if __name__ == "__main__":
    ejecutar_GET()
