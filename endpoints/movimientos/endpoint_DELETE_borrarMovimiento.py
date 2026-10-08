# endpoint_DELETE_borrarMovimiento.py
# DELETE /api/movimientos/{idMovimiento}
#
# Borra un movimiento y devuelve el saldo de la cuenta a como estaba
# antes de ese movimiento (y el avance de la meta, si tenia).
# Ejemplo: borrar un Ingreso de 100000 le resta 100000 a la cuenta.
# Si al deshacerlo la cuenta queda negativa, no se deja borrar.

import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from db_connection import ejecutar_transaccion, ErrorBaseDatos
from endpoints.movimientos.movimientos_comun import (
    consultar_movimiento_por_id,
    preparar_operaciones_de_saldo,
)
from validaciones.libreria_ahorro import solicitar_id


def borrar_movimiento(movimiento):
    """DELETE del movimiento + reversa del saldo, en una transaccion."""
    sql = "DELETE FROM movimientos WHERE idMovimiento = %s"
    operaciones = [(sql, (movimiento["idMovimiento"],))]
    operaciones += preparar_operaciones_de_saldo(movimiento, None)
    ejecutar_transaccion(operaciones)


def ejecutar_DELETE():
    """Entrada del script."""
    try:
        id_movimiento = solicitar_id("idMovimiento a borrar: ")

        movimiento = consultar_movimiento_por_id(id_movimiento)
        if movimiento is None:
            print(json.dumps(None, indent=2))
            return

        borrar_movimiento(movimiento)
        salida = {
            "idMovimiento eliminado": id_movimiento,
            "movimiento": movimiento,
        }
        print(json.dumps(salida, indent=2, ensure_ascii=False, default=str))
    except ValueError as error_validacion:
        print(str(error_validacion))
    except ErrorBaseDatos as error_bd:
        print("Error de base de datos: " + error_bd.mensaje)
    except Exception as error_inesperado:
        print("Error inesperado. Contacte al administrador. Detalle: " + str(error_inesperado))


if __name__ == "__main__":
    ejecutar_DELETE()
