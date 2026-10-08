# movimientos_comun.py
# Funciones que usan varios endpoints de movimientos.
#
# REGLA PRINCIPAL: cada vez que se crea, cambia o borra un movimiento,
# hay que mover tambien el saldo de la cuenta (cuentas.saldoActual) y,
# si el movimiento tiene meta, el avance de la meta (metas.montoActual).
# Todo eso se ejecuta en UNA transaccion: o se guarda todo o nada.
#
# La idea para no repetir codigo en POST, PUT, PATCH y DELETE:
#   cambio = efecto del movimiento nuevo - efecto del movimiento anterior
#     POST   -> no hay anterior (None)
#     DELETE -> no hay nuevo (None)
#     PUT / PATCH -> hay los dos

from decimal import Decimal

from db_connection import ejecutar_consulta
from validaciones.libreria_ahorro import efecto_en_saldo


SQL_ACTUALIZAR_SALDO = """
    UPDATE cuentas
    SET saldoActual = saldoActual + %s
    WHERE idCuenta = %s
"""

# MySQL aplica el SET de izquierda a derecha, entonces el CASE ya ve el
# montoActual nuevo. Si llega al objetivo la meta queda Cumplida, y si
# baja del objetivo (por ejemplo al borrar un ingreso) vuelve a EnProgreso.
SQL_ACTUALIZAR_META = """
    UPDATE metas
    SET montoActual = montoActual + %s,
        estado = CASE
            WHEN montoActual >= montoObjetivo THEN 'Cumplida'
            WHEN estado = 'Cumplida' THEN 'EnProgreso'
            ELSE estado
        END
    WHERE idMeta = %s
"""


def consultar_movimiento_por_id(id_movimiento):
    """Devuelve el movimiento como diccionario, o None si no existe."""
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
        WHERE idMovimiento = %s
    """
    return ejecutar_consulta(sql, (id_movimiento,), una_fila=True)


def validar_datos_contra_bd(datos):
    """
    Revisa en la base de datos lo que no se puede validar solo con el input:
    que la cuenta exista y este Activa, y que la meta o la categoria
    pertenezcan al mismo usuario dueño de la cuenta.
    Lanza ValueError con un mensaje claro si algo no cumple.
    """
    cuenta = ejecutar_consulta(
        "SELECT idCuenta, idUsuario, estado FROM cuentas WHERE idCuenta = %s",
        (datos["idCuenta"],), una_fila=True)
    if cuenta is None:
        raise ValueError(f"La cuenta {datos['idCuenta']} no existe.")
    if cuenta["estado"] != "Activa":
        raise ValueError(f"La cuenta {datos['idCuenta']} esta Inactiva, no recibe movimientos.")

    if datos.get("idMeta") is not None:
        meta = ejecutar_consulta(
            "SELECT idMeta, idUsuario FROM metas WHERE idMeta = %s",
            (datos["idMeta"],), una_fila=True)
        if meta is None:
            raise ValueError(f"La meta {datos['idMeta']} no existe.")
        if meta["idUsuario"] != cuenta["idUsuario"]:
            raise ValueError("La meta no pertenece al dueño de la cuenta.")

    if datos.get("idCategoria") is not None:
        categoria = ejecutar_consulta(
            "SELECT idCategoria, idUsuario FROM categorias WHERE idCategoria = %s",
            (datos["idCategoria"],), una_fila=True)
        if categoria is None:
            raise ValueError(f"La categoria {datos['idCategoria']} no existe.")
        if categoria["idUsuario"] != cuenta["idUsuario"]:
            raise ValueError("La categoria no pertenece al dueño de la cuenta.")


def _sumar(diccionario, llave, valor):
    if llave is not None:
        diccionario[llave] = diccionario.get(llave, Decimal("0")) + valor


def _efectos_del_movimiento(movimiento):
    """Cuanto le suma (o resta) el movimiento a cada cuenta y a cada meta."""
    cuentas = {}
    metas = {}
    if movimiento is None:
        return cuentas, metas

    # Decimal y no float porque es dinero: 0.1 + 0.2 en float no da 0.3 exacto
    monto = Decimal(str(movimiento["monto"]))
    _sumar(cuentas, movimiento["idCuenta"], efecto_en_saldo(movimiento["tipo"], monto))
    if movimiento["tipo"] == "Transferencia":
        _sumar(cuentas, movimiento.get("idCuentaDestino"), monto)
    _sumar(metas, movimiento.get("idMeta"), monto)
    return cuentas, metas


def preparar_operaciones_de_saldo(anterior, nuevo):
    """
    Devuelve la lista de UPDATE (sql, parametros) para cuentas y metas,
    lista para agregarla a ejecutar_transaccion().
    Antes revisa que ninguna cuenta quede con saldo negativo.
    """
    cuentas_anterior, metas_anterior = _efectos_del_movimiento(anterior)
    cuentas_nuevo, metas_nuevo = _efectos_del_movimiento(nuevo)

    cambios_cuentas = {}
    for id_cuenta, valor in cuentas_nuevo.items():
        _sumar(cambios_cuentas, id_cuenta, valor)
    for id_cuenta, valor in cuentas_anterior.items():
        _sumar(cambios_cuentas, id_cuenta, -valor)

    cambios_metas = {}
    for id_meta, valor in metas_nuevo.items():
        _sumar(cambios_metas, id_meta, valor)
    for id_meta, valor in metas_anterior.items():
        _sumar(cambios_metas, id_meta, -valor)

    operaciones = []
    for id_cuenta, cambio in cambios_cuentas.items():
        if cambio < 0:
            _validar_saldo_suficiente(id_cuenta, cambio)
        if cambio != 0:
            operaciones.append((SQL_ACTUALIZAR_SALDO, (cambio, id_cuenta)))
    for id_meta, cambio in cambios_metas.items():
        if cambio != 0:
            operaciones.append((SQL_ACTUALIZAR_META, (cambio, id_meta)))
    return operaciones


def _validar_saldo_suficiente(id_cuenta, cambio):
    # La tabla tambien tiene CHECK saldoActual >= 0, pero asi el usuario
    # recibe un mensaje claro en vez de un error de la base de datos.
    cuenta = ejecutar_consulta(
        "SELECT saldoActual FROM cuentas WHERE idCuenta = %s",
        (id_cuenta,), una_fila=True)
    if cuenta is None:
        raise ValueError(f"La cuenta {id_cuenta} no existe.")
    saldo = Decimal(str(cuenta["saldoActual"]))
    if saldo + cambio < 0:
        raise ValueError(
            f"Saldo insuficiente en la cuenta {id_cuenta}. "
            f"Saldo actual: {saldo}, la operacion necesita: {-cambio}")
