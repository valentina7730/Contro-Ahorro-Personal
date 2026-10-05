import re
import random

# ==========================================
# REQUERIMIENTO AHO-0013: Librería de Funciones
# ==========================================

def validar_documento(documento):
    """Valida que el documento sea estrictamente numérico."""
    patron = r'^\d+$'
    return bool(re.match(patron, str(documento)))

def calcular_interes(monto, tasa_anual, meses):
    """Calcula el interés simple de una cuenta o meta."""
    return monto * (tasa_anual / 100) * (meses / 12)

def actualizar_saldo(saldo_actual, monto_transaccion, es_ingreso=True):
    """Actualiza el saldo sumando o restando según el tipo de movimiento."""
    if es_ingreso:
        return saldo_actual + monto_transaccion
    else:
        return saldo_actual - monto_transaccion

def generar_id():
    """Genera un ID único numérico aleatorio de 6 dígitos."""
    return random.randint(100000, 999999)


# ==========================================
# REQUERIMIENTO AHO-0012: Validaciones y Try-Except
# ==========================================

# 1. Validaciones con Expresiones Regulares (Regex)
def validar_correo(correo):
    """Valida que el texto tenga un formato estándar de correo electrónico."""
    patron = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(patron, correo))

def validar_telefono(telefono):
    """Valida que el teléfono tenga exactamente 10 dígitos."""
    patron = r'^\d{10}$'
    return bool(re.match(patron, str(telefono)))

def validar_fecha(fecha):
    """Valida que la fecha tenga el formato YYYY-MM-DD."""
    patron = r'^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$'
    return bool(re.match(patron, fecha))

# 2. Bloques Try-Except para inputs numéricos sin break ni continue
def solicitar_id(mensaje):
    """Solicita un ID numérico controlando errores con banderas booleanas."""
    id_valido = False
    valor_id = 0
    
    while not id_valido:
        entrada = input(mensaje)
        try:
            valor_id = int(entrada)
            id_valido = True
        except ValueError:
            print("Error: El ID debe ser un número entero válido. Inténtelo nuevamente.")
            
    return valor_id

def solicitar_monto(mensaje):
    """Solicita un monto monetario controlando errores con banderas booleanas."""
    monto_valido = False
    valor_monto = 0.0
    
    while not monto_valido:
        entrada = input(mensaje)
        try:
            valor_monto = float(entrada)
            monto_valido = True
        except ValueError:
            print("Error: El monto no es válido. Solo se permiten números y punto para decimales.")
            
    return valor_monto