# libreria_ahorro.py
# Libreria propia del proyecto Control de Ahorro Personal.
#
# Aqui estan las validaciones y los calculos del negocio para que
# todos los endpoints usen las mismas reglas.
#   - validar_...   -> reciben un valor y devuelven True o False.
#   - solicitar_... -> piden el dato por consola y repiten hasta que
#                      sea valido (sin usar break ni continue).
#   - calcular_... / efecto_... -> calculos del negocio.

import math
import re
from datetime import datetime

TIPOS_MOVIMIENTO = ("Ingreso", "Retiro")
LARGO_MAX_DESCRIPCION = 200   # igual que varchar(200) en la tabla movimientos
MONTO_MAXIMO = 9999999999999.99   # lo maximo que cabe en decimal(15,2)


# ---------------------------------------------------------------------------
# CALCULOS DEL NEGOCIO
# ---------------------------------------------------------------------------

# Interes simple con la tasa MENSUAL de la cuenta (columna tasaInteresMensual).
# Ejemplo con los datos de prueba: 500000 al 0.5% durante 1 mes = 2500
def calcular_interes(saldo, tasa_mensual, meses):
    if saldo < 0 or tasa_mensual < 0 or meses < 0:
        return 0.0
    return round(saldo * (tasa_mensual / 100) * meses, 2)


# Dice cuanto cambia el saldo de la cuenta segun el tipo de movimiento.
# Ingreso e Interes suman, Retiro resta. En una Transferencia sale dinero
# de la cuenta origen (la cuenta destino se suma aparte).
def efecto_en_saldo(tipo, monto):
    if tipo in ("Ingreso", "Interes"):
        return monto
    return -monto


# ---------------------------------------------------------------------------
# VALIDACIONES (devuelven True o False)
# Se usa re.fullmatch para que toda la cadena cumpla el patron.
# ---------------------------------------------------------------------------

# Documento de 6 a 12 digitos (igual que el CHECK de la tabla usuarios)
def validar_documento(documento):
    return re.fullmatch(r"\d{6,12}", str(documento).strip()) is not None


# usuario@dominio.algo  (el dominio puede tener varios puntos: mail.com.co)
def validar_correo(correo):
    patron = r"[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+"
    return re.fullmatch(patron, str(correo).strip()) is not None


# Celular de 10 digitos
def validar_telefono(telefono):
    return re.fullmatch(r"\d{10}", str(telefono).strip()) is not None


# Fecha con formato AAAA-MM-DD y que exista en el calendario (no 2026-02-30)
def validar_fecha(fecha_texto):
    if not isinstance(fecha_texto, str):
        return False
    try:
        datetime.strptime(fecha_texto.strip(), "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validar_tipo_movimiento(tipo):
    return str(tipo).strip().capitalize() in TIPOS_MOVIMIENTO


# ---------------------------------------------------------------------------
# CAPTURAS POR CONSOLA (repiten hasta que el dato sea valido)
# ---------------------------------------------------------------------------

def solicitar_id(mensaje):
    valido = False
    valor_id = 0
    while not valido:
        entrada = input(mensaje).strip()
        if entrada.isdigit() and int(entrada) > 0:
            valor_id = int(entrada)
            valido = True
        else:
            print("El ID debe ser un numero entero mayor a 0.")
    return valor_id


# Igual que solicitar_id pero se puede dejar vacio (devuelve None).
# Sirve para idMeta e idCategoria, que no son obligatorios.
def solicitar_id_opcional(mensaje):
    valido = False
    valor_id = None
    while not valido:
        entrada = input(mensaje).strip()
        if entrada == "":
            valido = True
        elif entrada.isdigit() and int(entrada) > 0:
            valor_id = int(entrada)
            valido = True
        else:
            print("Escriba un numero entero mayor a 0 o deje vacio.")
    return valor_id


# El monto debe ser mayor a 0 y tener maximo 2 decimales
# (la tabla tiene CHECK monto > 0 y el campo es decimal(15,2)).
def solicitar_monto(mensaje):
    valido = False
    valor_monto = 0.0
    while not valido:
        entrada = input(mensaje).strip()
        try:
            valor_monto = float(entrada)
            if not math.isfinite(valor_monto) or valor_monto <= 0:
                print("El monto debe ser mayor a 0.")
            elif valor_monto > MONTO_MAXIMO:
                print("El monto es demasiado grande.")
            elif "." in entrada and len(entrada.split(".")[1]) > 2:
                print("El monto puede tener maximo 2 decimales.")
            else:
                valido = True
        except ValueError:
            print("Error: use solo numeros y punto decimal. Ejemplo: 150000.50")
    return valor_monto


# Devuelve la fecha como texto "AAAA-MM-DD", que es lo que recibe MySQL
def solicitar_fecha(mensaje):
    valido = False
    fecha_texto = ""
    while not valido:
        entrada = input(mensaje).strip()
        if validar_fecha(entrada):
            fecha_texto = entrada
            valido = True
        else:
            print("Fecha invalida. Use el formato AAAA-MM-DD.")
    return fecha_texto


# Acepta "ingreso", "INGRESO", " Ingreso " y lo deja como "Ingreso"
def solicitar_tipo_movimiento(mensaje):
    valido = False
    tipo_movimiento = ""
    while not valido:
        entrada = input(mensaje).strip().capitalize()
        if entrada in TIPOS_MOVIMIENTO:
            tipo_movimiento = entrada
            valido = True
        else:
            print("Opcion invalida. Debe ser 'Ingreso' o 'Retiro'.")
    return tipo_movimiento


# La descripcion es opcional: si se deja vacia se guarda NULL
def solicitar_descripcion(mensaje):
    valido = False
    descripcion = None
    while not valido:
        entrada = input(mensaje).strip()
        if len(entrada) > LARGO_MAX_DESCRIPCION:
            print(f"La descripcion puede tener maximo {LARGO_MAX_DESCRIPCION} caracteres.")
        else:
            if entrada != "":
                descripcion = entrada
            valido = True
    return descripcion
