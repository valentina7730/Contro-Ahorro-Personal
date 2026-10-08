# endpoint_PATCH_actualizaMontoMovimiento.py
# PATCH /api/movimientos/{idMovimiento}
#
# Cambia SOLO el monto de un movimiento (diferencia con PUT: PUT cambia todo).
# El saldo de la cuenta se ajusta con la diferencia entre el monto nuevo y
# el anterior. Ejemplo: un Retiro de 50000 pasa a 80000 -> la cuenta baja 30000.

import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from db_connection import ejecutar_transaccion, ErrorBaseDatos
from endpoints.movimientos.movimientos_comun import (
    consultar_movimiento_por_id,
    preparar_operaciones_de_saldo,
)
from validaciones.libreria_ahorro import solicitar_id, solicitar_monto


def actualizar_monto(anterior, monto_nuevo):
    """UPDATE solo de la columna monto + ajuste de saldos, en una transaccion."""
    sql = """
        UPDATE movimientos
        SET monto = %s
        WHERE idMovimiento = %s
    """
    nuevo = dict(anterior)          # copia del movimiento con el monto cambiado
    nuevo["monto"] = monto_nuevo

    operaciones = [(sql, (monto_nuevo, anterior["idMovimiento"]))]
    operaciones += preparar_operaciones_de_saldo(anterior, nuevo)
    ejecutar_transaccion(operaciones)


def ejecutar_PATCH():
    """Entrada del script."""
    try:
        id_movimiento = solicitar_id("idMovimiento a actualizar: ")

        anterior = consultar_movimiento_por_id(id_movimiento)
        if anterior is None:
            print(json.dumps(None, indent=2))
            return

        print(f"Monto actual: {anterior['monto']}")
        monto_nuevo = solicitar_monto("Nuevo monto: ")
        actualizar_monto(anterior, monto_nuevo)

        salida = {
            "idMovimiento": id_movimiento,
            "monto_anterior": anterior["monto"],
            "monto_nuevo": monto_nuevo,
        }
        print(json.dumps(salida, indent=2, ensure_ascii=False, default=str))
    except ValueError as error_validacion:
        print(str(error_validacion))
    except ErrorBaseDatos as error_bd:
        print("Error de base de datos: " + error_bd.mensaje)
    except Exception as error_inesperado:
        print("Error inesperado. Contacte al administrador. Detalle: " + str(error_inesperado))


if __name__ == "__main__":
    ejecutar_PATCH()
