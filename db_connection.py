"""
conexion.py - CAPA 2: Conexión a la base de datos
==================================================

Proyecto: Control de Ahorro Personal (REQUERIMIENTOS_09)
Materia:  Programación V

Responsabilidad de esta capa
----------------------------
Este módulo es el ÚNICO que habla directamente con MySQL. Las demás capas
(lógica de negocio y endpoints) nunca crean conexiones ni cursores: solo
llaman a las funciones públicas de este archivo.

    Capa 1: .env               -> guarda host, puerto, usuario, password y BD
    Capa 2: conexion.py        -> lee el .env, abre/cierra conexiones y ejecuta SQL
    Capa 3: libreria_ahorro.py -> reglas del negocio (usa las funciones de aquí)
    Capa 4: endpoints          -> reciben HTTP y responden JSON

Funciones públicas
------------------
    obtener_conexion()                       -> abre una conexión nueva
    ejecutar_consulta(sql, parametros)       -> SELECT, devuelve lista de diccionarios
    ejecutar_comando(sql, parametros)        -> INSERT / UPDATE / DELETE con commit
    ejecutar_transaccion(operaciones)        -> varias sentencias: todas o ninguna
    probar_conexion()                        -> verifica que todo esté bien configurado

Seguridad (sanitización)
------------------------
Todas las funciones reciben el SQL con marcadores %s y los valores aparte,
en `parametros`. El conector escapa los valores, lo que evita la inyección SQL.

    BIEN:  ejecutar_consulta("SELECT * FROM usuarios WHERE idUsuario = %s", (id_usuario,))
    MAL:   ejecutar_consulta(f"SELECT * FROM usuarios WHERE idUsuario = {id_usuario}")

Además, el conector rechaza varias sentencias en una sola llamada, así que
un texto como "1; DROP TABLE usuarios" no se puede ejecutar.

Manejo de errores
-----------------
Cualquier error de MySQL se convierte en ErrorBaseDatos, que trae un mensaje
en español y el código original de MySQL. Los endpoints solo deben capturar
ErrorBaseDatos y responder `error.a_diccionario()` como JSON.

Dependencias (ver requirements.txt)
-----------------------------------
    pip install mysql-connector-python python-dotenv
"""

import json
import os
from datetime import date, datetime, time, timedelta
from decimal import Decimal

import mysql.connector
from mysql.connector import Error as MySQLError
from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

# El .env se busca en la misma carpeta de este archivo, sin importar desde
# qué carpeta se ejecute el programa en la terminal de VS Code.
RUTA_ENV = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

# Variables que obligatoriamente deben existir en el .env
VARIABLES_REQUERIDAS = ("DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME")

# Segundos máximos que se espera al servidor antes de rendirse
TIEMPO_ESPERA_CONEXION = 10

# Traducción de los códigos de error de MySQL más comunes a mensajes claros.
# Cualquier código que no esté aquí usa un mensaje genérico.
MENSAJES_ERROR_MYSQL = {
    1045: "Usuario o contraseña de la base de datos incorrectos. Revise el archivo .env.",
    1049: "La base de datos no existe. Ejecute primero creacion_schema.sql.",
    2003: "No se pudo conectar al servidor MySQL. Verifique que el servicio esté encendido.",
    2005: "No se encontró el servidor MySQL. Revise DB_HOST en el archivo .env.",
    1142: "El usuario de la base de datos no tiene permiso para esta operación.",
    1048: "Falta un dato obligatorio.",
    1062: "Ya existe un registro con ese valor (por ejemplo, documento o correo repetido).",
    1265: "Un valor no es válido para el campo (por ejemplo, un estado o tipo no permitido).",
    1406: "Uno de los textos supera la longitud máxima permitida.",
    1451: "No se puede eliminar o modificar: el registro tiene información asociada.",
    1452: "El registro relacionado no existe (revise los id enviados).",
    3819: "Los datos no cumplen una regla de la base de datos.",
}

# Errores en los que conviene mostrar también el detalle técnico de MySQL,
# porque indica qué regla o qué campo falló (por ejemplo, chk_cuentas_saldo_actual).
ERRORES_CON_DETALLE = (1048, 1062, 1265, 1406, 3819)


# ---------------------------------------------------------------------------
# Excepción propia de la capa
# ---------------------------------------------------------------------------

class ErrorBaseDatos(Exception):
    """
    Error controlado de la capa de base de datos.

    Atributos:
        mensaje (str): explicación en español, lista para mostrar al usuario.
        codigo_mysql (int | None): código original de MySQL (None si el error
            no vino de MySQL, por ejemplo un .env mal configurado).
    """

    def __init__(self, mensaje, codigo_mysql=None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo_mysql = codigo_mysql

    def a_diccionario(self):
        """Devuelve el error en un formato listo para responder como JSON."""
        return {"ok": False, "error": self.mensaje, "codigoMysql": self.codigo_mysql}


# ---------------------------------------------------------------------------
# Funciones internas (empiezan con _ : no se usan fuera de este archivo)
# ---------------------------------------------------------------------------

def _convertir_error(error):
    """
    Convierte un error de mysql.connector en un ErrorBaseDatos con mensaje claro.

    Parámetros:
        error (mysql.connector.Error): error original lanzado por el conector.

    Retorna:
        ErrorBaseDatos
    """
    codigo = getattr(error, "errno", None)
    detalle = getattr(error, "msg", str(error))
    mensaje = MENSAJES_ERROR_MYSQL.get(codigo, f"Error de base de datos: {detalle}")
    if codigo in ERRORES_CON_DETALLE:
        mensaje = f"{mensaje} Detalle: {detalle}"
    return ErrorBaseDatos(mensaje, codigo)


def _validar_sql(sql, parametros):
    """
    Revisa que el SQL sea un texto con contenido y que los parámetros
    tengan un tipo que el conector acepte (tupla, lista, diccionario o None).

    Lanza:
        ErrorBaseDatos si algo no cumple.
    """
    if not isinstance(sql, str) or not sql.strip():
        raise ErrorBaseDatos("La sentencia SQL está vacía o no es un texto.")
    if parametros is not None and not isinstance(parametros, (tuple, list, dict)):
        raise ErrorBaseDatos(
            "Los parámetros deben ir en una tupla, lista o diccionario. "
            "Para un solo valor use una tupla con coma: (valor,)"
        )


def _deshacer(conexion):
    """Hace rollback si la conexión sigue abierta. Nunca lanza errores."""
    try:
        if conexion is not None and conexion.is_connected():
            conexion.rollback()
    except MySQLError:
        pass


def _cerrar_recursos(cursor, conexion):
    """Cierra el cursor y la conexión si existen. Nunca lanza errores."""
    try:
        if cursor is not None:
            cursor.close()
    except MySQLError:
        pass
    try:
        if conexion is not None and conexion.is_connected():
            conexion.close()
    except MySQLError:
        pass


def _normalizar_valor(valor):
    """
    Convierte los tipos que entrega MySQL a tipos que se pueden pasar a JSON.

        DECIMAL            -> float      (ej: 902500.0)
        DATE / DATETIME    -> texto ISO  (ej: "2026-10-04")
        TIME / TIMEDELTA   -> texto
        bytes              -> texto
    """
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, (datetime, date, time)):
        return valor.isoformat()
    if isinstance(valor, timedelta):
        return str(valor)
    if isinstance(valor, (bytes, bytearray)):
        return valor.decode("utf-8", errors="replace")
    return valor


def normalizar_fila(fila):
    """
    Aplica _normalizar_valor a todas las columnas de una fila.

    Parámetros:
        fila (dict): fila tal como la devuelve un cursor con dictionary=True.

    Retorna:
        dict: la misma fila, lista para json.dumps().
    """
    return {columna: _normalizar_valor(valor) for columna, valor in fila.items()}


# ---------------------------------------------------------------------------
# Configuración y conexión
# ---------------------------------------------------------------------------

def cargar_configuracion():
    """
    Lee el archivo .env y arma el diccionario de configuración para MySQL.

    Retorna:
        dict con las llaves host, port, user, password y database.

    Lanza:
        ErrorBaseDatos si no existe el .env, falta una variable o el puerto
        no es un número válido.
    """
    if not os.path.isfile(RUTA_ENV):
        raise ErrorBaseDatos(f"No se encontró el archivo .env en: {RUTA_ENV}")

    load_dotenv(RUTA_ENV, override=True)

    faltantes = [nombre for nombre in VARIABLES_REQUERIDAS if not os.getenv(nombre, "").strip()]
    if faltantes:
        raise ErrorBaseDatos(f"Faltan variables en el archivo .env: {', '.join(faltantes)}")

    try:
        puerto = int(os.getenv("DB_PORT").strip())
    except ValueError:
        raise ErrorBaseDatos("DB_PORT en el archivo .env debe ser un número entero.") from None

    if not 1 <= puerto <= 65535:
        raise ErrorBaseDatos("DB_PORT en el archivo .env debe estar entre 1 y 65535.")

    return {
        "host": os.getenv("DB_HOST").strip(),
        "port": puerto,
        "user": os.getenv("DB_USER").strip(),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME").strip(),
    }


def obtener_conexion():
    """
    Abre una conexión nueva a MySQL con los datos del .env.

    La conexión se abre con autocommit desactivado: los cambios solo quedan
    guardados cuando se hace commit (las funciones de abajo ya lo hacen).

    Retorna:
        mysql.connector.connection.MySQLConnection

    Lanza:
        ErrorBaseDatos si no se puede conectar.
    """
    configuracion = cargar_configuracion()
    try:
        return mysql.connector.connect(
            **configuracion,
            autocommit=False,
            charset="utf8mb4",
            collation="utf8mb4_0900_ai_ci",
            connection_timeout=TIEMPO_ESPERA_CONEXION,
        )
    except MySQLError as error:
        raise _convertir_error(error) from error


# ---------------------------------------------------------------------------
# Ejecución de sentencias
# ---------------------------------------------------------------------------

def ejecutar_consulta(sql, parametros=None, una_fila=False):
    """
    Ejecuta un SELECT y devuelve los resultados listos para JSON.

    Parámetros:
        sql (str): consulta con marcadores %s.
        parametros (tuple | list | dict | None): valores para los %s.
        una_fila (bool): si es True devuelve solo la primera fila (o None).

    Retorna:
        list[dict]  si una_fila es False (lista vacía si no hay resultados).
        dict | None si una_fila es True.

    Ejemplo:
        cuenta = ejecutar_consulta(
            "SELECT idCuenta, saldoActual, estado FROM cuentas WHERE idCuenta = %s",
            (1,), una_fila=True)
        # {'idCuenta': 1, 'saldoActual': 902500.0, 'estado': 'Activa'}
    """
    _validar_sql(sql, parametros)
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(sql, parametros or ())
        filas = [normalizar_fila(fila) for fila in cursor.fetchall()]
        if una_fila:
            return filas[0] if filas else None
        return filas
    except MySQLError as error:
        raise _convertir_error(error) from error
    finally:
        _cerrar_recursos(cursor, conexion)


def ejecutar_comando(sql, parametros=None):
    """
    Ejecuta un INSERT, UPDATE o DELETE y guarda el cambio (commit).
    Si algo falla, deshace el cambio (rollback).

    Parámetros:
        sql (str): sentencia con marcadores %s.
        parametros (tuple | list | dict | None): valores para los %s.

    Retorna:
        dict con:
            filasAfectadas (int): 0 significa que ningún registro coincidió
                                  (útil para responder "no encontrado").
            ultimoId (int | None): id generado por un INSERT.

    Ejemplo:
        resultado = ejecutar_comando(
            "UPDATE cuentas SET estado = %s WHERE idCuenta = %s", ("Inactiva", 2))
        # {'filasAfectadas': 1, 'ultimoId': None}
    """
    _validar_sql(sql, parametros)
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(sql, parametros or ())
        conexion.commit()
        return {"filasAfectadas": cursor.rowcount, "ultimoId": cursor.lastrowid or None}
    except MySQLError as error:
        _deshacer(conexion)
        raise _convertir_error(error) from error
    finally:
        _cerrar_recursos(cursor, conexion)


def ejecutar_transaccion(operaciones):
    """
    Ejecuta varias sentencias como una sola unidad: o se guardan todas o
    no se guarda ninguna. Es obligatoria cuando un movimiento cambia varias
    tablas a la vez (AHO-0004 y AHO-0006): insertar el movimiento, actualizar
    el saldo de la cuenta y actualizar el monto de la meta.

    Parámetros:
        operaciones (list[tuple]): lista de pares (sql, parametros).

    Retorna:
        list[dict]: un resultado por operación, en el mismo orden, con
        filasAfectadas y ultimoId.

    Ejemplo (ingreso de 100.000 a la cuenta 1, asociado a la meta 1):
        ejecutar_transaccion([
            ("INSERT INTO movimientos (idCuenta, tipo, monto, fechaMovimiento, idMeta) "
             "VALUES (%s, %s, %s, %s, %s)", (1, "Ingreso", 100000, "2026-10-04", 1)),
            ("UPDATE cuentas SET saldoActual = saldoActual + %s WHERE idCuenta = %s",
             (100000, 1)),
            ("UPDATE metas SET montoActual = montoActual + %s WHERE idMeta = %s",
             (100000, 1)),
        ])

    Nota: si un retiro deja el saldo negativo, el CHECK de la tabla cuentas
    lo rechaza y TODA la transacción se deshace, incluido el INSERT.
    """
    if not isinstance(operaciones, (list, tuple)) or len(operaciones) == 0:
        raise ErrorBaseDatos("La transacción debe recibir una lista con al menos una operación.")
    for operacion in operaciones:
        if not isinstance(operacion, (list, tuple)) or len(operacion) != 2:
            raise ErrorBaseDatos("Cada operación debe ser un par (sql, parametros).")
        _validar_sql(operacion[0], operacion[1])

    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        resultados = []
        for sql, parametros in operaciones:
            cursor.execute(sql, parametros or ())
            resultados.append({"filasAfectadas": cursor.rowcount, "ultimoId": cursor.lastrowid or None})
        conexion.commit()
        return resultados
    except MySQLError as error:
        _deshacer(conexion)
        raise _convertir_error(error) from error
    finally:
        _cerrar_recursos(cursor, conexion)


# ---------------------------------------------------------------------------
# Diagnóstico
# ---------------------------------------------------------------------------

def probar_conexion():
    """
    Verifica que el .env, el usuario y la base de datos estén bien.

    Retorna:
        dict con ok=True, versión de MySQL, base de datos, usuario conectado
        y cantidad de tablas y vistas encontradas. Si algo falla, devuelve
        el diccionario de error (ok=False) en lugar de lanzar la excepción.
    """
    try:
        servidor = ejecutar_consulta(
            "SELECT VERSION() AS version, DATABASE() AS baseDatos, CURRENT_USER() AS usuario",
            una_fila=True,
        )
        objetos = ejecutar_consulta(
            "SELECT "
            "  SUM(table_type = 'BASE TABLE') AS tablas, "
            "  SUM(table_type = 'VIEW') AS vistas "
            "FROM information_schema.tables WHERE table_schema = DATABASE()",
            una_fila=True,
        )
        return {
            "ok": True,
            "mensaje": "Conexión exitosa a la base de datos.",
            "versionMysql": servidor["version"],
            "baseDatos": servidor["baseDatos"],
            "usuario": servidor["usuario"],
            "tablas": int(objetos["tablas"] or 0),
            "vistas": int(objetos["vistas"] or 0),
        }
    except ErrorBaseDatos as error:
        return error.a_diccionario()


# Al ejecutar "python conexion.py" se hace la prueba y se muestra en JSON.
if __name__ == "__main__":
    print(json.dumps(probar_conexion(), ensure_ascii=False, indent=4))
