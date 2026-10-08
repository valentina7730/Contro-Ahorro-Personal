# endpoint_POST_nuevoMovimiento.py
# POST /api/movimientos
#
# Registra un Ingreso o un Retiro en una cuenta de ahorro.
#   - Ingreso: se puede asociar a una meta (idMeta) y suma al avance de la meta.
#   - Retiro: se puede asociar a una categoria de gasto (idCategoria).
# El INSERT y la actualizacion del saldo van en la misma transaccion.
#
# POST no es idempotente: si se ejecuta dos veces con los mismos datos
# se crean dos movimientos (y el saldo se mueve dos veces).

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
    solicitar_descripcion,
    solicitar_fecha,
    solicitar_id,
    solicitar_id_opcional,
    solicitar_monto,
    solicitar_tipo_movimiento,
)


def capturar_datos():
    """Pide los datos del movimiento nuevo."""
    id_cuenta = solicitar_id("idCuenta: ")
    tipo = solicitar_tipo_movimiento("Tipo (Ingreso/Retiro): ")
    monto = solicitar_monto("Monto: ")
    fecha = solicitar_fecha("Fecha (AAAA-MM-DD): ")
    descripcion = solicitar_descripcion("Descripcion (Enter para dejar vacia): ")

    # La tabla solo deja meta en Ingresos y categoria en Retiros
    id_meta = None
    id_categoria = None
    if tipo == "Ingreso":
        id_meta = solicitar_id_opcional("idMeta (Enter si no aplica): ")
    else:
        id_categoria = solicitar_id_opcional("idCategoria (Enter si no aplica): ")

    return {
        "idCuenta": id_cuenta,
        "tipo": tipo,
        "monto": monto,
        "fechaMovimiento": fecha,
        "descripcion": descripcion,
        "idMeta": id_meta,
        "idCategoria": id_categoria,
        "idCuentaDestino": None,
    }


def insertar_movimiento(datos):
    """INSERT del movimiento + UPDATE del saldo (y de la meta) en una transaccion."""
    sql = """
        INSERT INTO movimientos (
            idCuenta,
            tipo,
            monto,
            fechaMovimiento,
            descripcion,
            idMeta,
            idCategoria
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    parametros = (
        datos["idCuenta"],
        datos["tipo"],
        datos["monto"],
        datos["fechaMovimiento"],
        datos["descripcion"],
        datos["idMeta"],
        datos["idCategoria"],
    )
    operaciones = [(sql, parametros)]
    operaciones += preparar_operaciones_de_saldo(None, datos)

    resultados = ejecutar_transaccion(operaciones)
    return resultados[0]["ultimoId"]   # el id generado por el INSERT


def ejecutar_POST():
    """Entrada del script."""
    try:
        datos = capturar_datos()
        validar_datos_contra_bd(datos)

        id_nuevo = insertar_movimiento(datos)
        if not id_nuevo:
            raise RuntimeError("No se pudo obtener el idMovimiento generado")

        movimiento_creado = consultar_movimiento_por_id(id_nuevo)
        print(json.dumps(movimiento_creado, indent=2, ensure_ascii=False, default=str))
    except ValueError as error_validacion:
        print(str(error_validacion))
    except ErrorBaseDatos as error_bd:
        print("Error de base de datos: " + error_bd.mensaje)
    except Exception as error_inesperado:
        print("Error inesperado. Contacte al administrador. Detalle: " + str(error_inesperado))


if __name__ == "__main__":
    ejecutar_POST()
