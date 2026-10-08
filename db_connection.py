# db_connection.py
# Conexion a la base de datos MySQL del proyecto Control de Ahorro Personal.
#
# Este es el UNICO archivo que abre conexiones a MySQL. Los endpoints no
# crean cursores, solo llaman a estas funciones:
#   ejecutar_consulta(sql, parametros)   -> SELECT, devuelve lista de diccionarios
#   ejecutar_comando(sql, parametros)    -> un INSERT / UPDATE / DELETE con commit
#   ejecutar_transaccion(operaciones)    -> varias sentencias: se guardan todas o ninguna
#   probar_conexion()                    -> para revisar que el .env este bien
#
# Los datos de conexion (host, puerto, usuario, password, base) se leen del
# archivo .env, que NO se sube a GitHub (esta en el .gitignore).
#
# Seguridad: el SQL siempre lleva %s y los valores van aparte en "parametros".
# El conector escapa los valores y asi se evita la inyeccion SQL.
#   BIEN: ejecutar_consulta("SELECT * FROM usuarios WHERE idUsuario = %s", (id_usuario,))
#   MAL:  ejecutar_consulta(f"SELECT * FROM usuarios WHERE idUsuario = {id_usuario}")
#
# Instalar dependencias: pip install -r requirements.txt

import json
import os
from datetime import date, datetime, time, timedelta
from decimal import Decimal

import mysql.connector
from mysql.connector import Error as MySQLError
from dotenv import load_dotenv


# El .env se busca en la misma carpeta de este archivo, asi funciona sin
# importar desde que carpeta se ejecute el programa.
RUTA_ENV = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
VARIABLES_REQUERIDAS = ("DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME")
TIEMPO_ESPERA_CONEXION = 10   # segundos

# Mensajes en español para los errores de MySQL mas comunes
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

# En estos errores se muestra tambien el detalle de MySQL porque dice que
# campo o que regla fallo (por ejemplo chk_cuentas_saldo_actual)
ERRORES_CON_DETALLE = (1048, 1062, 1265, 1406, 3819)


class ErrorBaseDatos(Exception):
    """Error de la base de datos con mensaje en español y el codigo de MySQL."""

    def __init__(self, mensaje, codigo_mysql=None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo_mysql = codigo_mysql

    def a_diccionario(self):
        return {"ok": False, "error": self.mensaje, "codigoMysql": self.codigo_mysql}


# ---------------------------------------------------------------------------
# Funciones internas (las que empiezan con _ solo se usan en este archivo)
# ---------------------------------------------------------------------------

def _convertir_error(error):
    codigo = getattr(error, "errno", None)
    detalle = getattr(error, "msg", str(error))
    mensaje = MENSAJES_ERROR_MYSQL.get(codigo, f"Error de base de datos: {detalle}")
    if codigo in ERRORES_CON_DETALLE:
        mensaje = f"{mensaje} Detalle: {detalle}"
    return ErrorBaseDatos(mensaje, codigo)


def _validar_sql(sql, parametros):
    if not isinstance(sql, str) or not sql.strip():
        raise ErrorBaseDatos("La sentencia SQL está vacía o no es un texto.")
    if parametros is not None and not isinstance(parametros, (tuple, list, dict)):
        raise ErrorBaseDatos(
            "Los parámetros deben ir en una tupla, lista o diccionario. "
            "Para un solo valor use una tupla con coma: (valor,)")


def _deshacer(conexion):
    try:
        if conexion is not None and conexion.is_connected():
            conexion.rollback()
    except MySQLError:
        pass


def _cerrar_recursos(cursor, conexion):
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


# MySQL devuelve Decimal, date, etc. que json.dumps no sabe convertir.
# Aqui se pasan a float y a texto.
def _normalizar_valor(valor):
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, (datetime, date, time)):
        return valor.isoformat()
    if isinstance(valor, timedelta):
        return str(valor)
    if isinstance(valor, (bytes, bytearray)):
        return valor.decode("utf-8", errors="replace")
    return valor


def _normalizar_fila(fila):
    return {columna: _normalizar_valor(valor) for columna, valor in fila.items()}


# ---------------------------------------------------------------------------
# Configuracion y conexion
# ---------------------------------------------------------------------------

def cargar_configuracion():
    """Lee el .env y devuelve el diccionario que necesita mysql.connector."""
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
    """Abre una conexion nueva. autocommit=False: nada se guarda sin commit."""
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
# Ejecucion de sentencias
# ---------------------------------------------------------------------------

def ejecutar_consulta(sql, parametros=None, una_fila=False):
    """
    Ejecuta un SELECT.
    Devuelve una lista de diccionarios, o si una_fila=True solo el
    primer diccionario (None si no encontro nada).
    """
    _validar_sql(sql, parametros)
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(sql, parametros or ())
        filas = [_normalizar_fila(fila) for fila in cursor.fetchall()]
        if una_fila:
            return filas[0] if filas else None
        return filas
    except MySQLError as error:
        raise _convertir_error(error) from error
    finally:
        _cerrar_recursos(cursor, conexion)


def ejecutar_comando(sql, parametros=None):
    """
    Ejecuta un INSERT, UPDATE o DELETE y hace commit (rollback si falla).
    Devuelve {"filasAfectadas": n, "ultimoId": id del INSERT o None}.
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
    Ejecuta varias sentencias en la misma conexion y hace UN solo commit
    al final. Si cualquiera falla se hace rollback y no queda nada guardado.

    operaciones: lista de pares (sql, parametros). Ejemplo:
        ejecutar_transaccion([
            ("INSERT INTO movimientos (...) VALUES (%s, ...)", (...)),
            ("UPDATE cuentas SET saldoActual = saldoActual + %s WHERE idCuenta = %s", (100000, 1)),
        ])
    Devuelve una lista con un resultado por operacion (filasAfectadas, ultimoId).
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
# Prueba de conexion:  python db_connection.py
# ---------------------------------------------------------------------------

def probar_conexion():
    try:
        servidor = ejecutar_consulta(
            "SELECT VERSION() AS version, DATABASE() AS baseDatos, CURRENT_USER() AS usuario",
            una_fila=True)
        objetos = ejecutar_consulta(
            "SELECT SUM(table_type = 'BASE TABLE') AS tablas, SUM(table_type = 'VIEW') AS vistas "
            "FROM information_schema.tables WHERE table_schema = DATABASE()",
            una_fila=True)
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


if __name__ == "__main__":
    print(json.dumps(probar_conexion(), ensure_ascii=False, indent=4))
