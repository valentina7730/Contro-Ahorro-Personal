# endpoint_PUT_actualizaMovimiento.py
# PUT /api/movimientos/{idMovimiento}
#
# Reemplaza TODOS los datos de un movimiento.
# Primero se deshace el efecto del movimiento anterior en el saldo y
# luego se aplica el del movimiento nuevo (todo en una transaccion).
#
# Solo se reemplazan Ingresos y Retiros. Las Transferencias y los
# Intereses los genera otro proceso, por eso no se editan aqui.
#
# PUT si es idempotente: repetirlo con los mismos datos deja el
# movimiento y el saldo igual que la primera vez.

import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from db_connection import ejecutar_transaccion, ErrorBaseDatos
from endpoints.movimientos.movimientos_comun import (
    consultar_movimiento_por_id,
    preparar_operaciones_de_saldo,
    validar_datos_contra_bd,
)
from validaciones.libreria_ahorro import (
    TIPOS_MOVIMIENTO,
    solicitar_descripcion,
    solicitar_fecha,
    solicitar_id,
    solicitar_id_opcional,
    solicitar_monto,
    solicitar_tipo_movimiento,
)


def capturar_datos_nuevos(id_movimiento):
    """Pide todos los valores nuevos del movimiento."""
    id_cuenta = solicitar_id("Nuevo idCuenta: ")
    tipo = solicitar_tipo_movimiento("Nuevo tipo (Ingreso/Retiro): ")
    monto = solicitar_monto("Nuevo monto: ")
    fecha = solicitar_fecha("Nueva fecha (AAAA-MM-DD): ")
    descripcion = solicitar_descripcion("Nueva descripcion (Enter para dejar vacia): ")

    id_meta = None
    id_categoria = None
    if tipo == "Ingreso":
        id_meta = solicitar_id_opcional("idMeta (Enter si no aplica): ")
    else:
        id_categoria = solicitar_id_opcional("idCategoria (Enter si no aplica): ")

    return {
        "idMovimiento": id_movimiento,
        "idCuenta": id_cuenta,
        "tipo": tipo,
        "monto": monto,
        "fechaMovimiento": fecha,
        "descripcion": descripcion,
        "idMeta": id_meta,
        "idCategoria": id_categoria,
        "idCuentaDestino": None,
    }


def reemplazar_movimiento(anterior, nuevo):
    """UPDATE de todas las columnas + ajuste de saldos, en una transaccion."""
    sql = """
        UPDATE movimientos
        SET
            idCuenta = %s,
            tipo = %s,
            monto = %s,
            fechaMovimiento = %s,
            descripcion = %s,
            idMeta = %s,
            idCategoria = %s,
            idCuentaDestino = NULL
        WHERE idMovimiento = %s
    """
    # El id va de ultimo porque es el del WHERE
    parametros = (
        nuevo["idCuenta"],
        nuevo["tipo"],
        nuevo["monto"],
        nuevo["fechaMovimiento"],
        nuevo["descripcion"],
        nuevo["idMeta"],
        nuevo["idCategoria"],
        nuevo["idMovimiento"],
    )
    operaciones = [(sql, parametros)]
    operaciones += preparar_operaciones_de_saldo(anterior, nuevo)
    ejecutar_transaccion(operaciones)


def ejecutar_PUT():
    """Entrada del script."""
    try:
        id_movimiento = solicitar_id("idMovimiento a reemplazar: ")

        anterior = consultar_movimiento_por_id(id_movimiento)
        if anterior is None:
            print(json.dumps(None, indent=2))
            return
        if anterior["tipo"] not in TIPOS_MOVIMIENTO:
            raise ValueError(
                f"El movimiento {id_movimiento} es de tipo {anterior['tipo']} "
                "y no se puede reemplazar. Solo se reemplazan Ingresos y Retiros.")

        nuevo = capturar_datos_nuevos(id_movimiento)
        validar_datos_contra_bd(nuevo)
        reemplazar_movimiento(anterior, nuevo)

        salida = {
            "antes": anterior,
            "despues": consultar_movimiento_por_id(id_movimiento),
        }
        print(json.dumps(salida, indent=2, ensure_ascii=False, default=str))
    except ValueError as error_validacion:
        print(str(error_validacion))
    except ErrorBaseDatos as error_bd:
        print("Error de base de datos: " + error_bd.mensaje)
    except Exception as error_inesperado:
        print("Error inesperado. Contacte al administrador. Detalle: " + str(error_inesperado))


if __name__ == "__main__":
    ejecutar_PUT()
