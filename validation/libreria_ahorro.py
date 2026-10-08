import re
import random
from datetime import datetime

# --- Lógica de negocio y cálculos ---

def validar_documento(documento):
    # Cédula o documento entre 6 y 12 dígitos (regla BD)
    patron = r'^\d{6,12}$'
    return bool(re.match(patron, str(documento)))

def calcular_interes(monto, tasa_anual, meses):
    if monto < 0 or tasa_anual < 0 or meses < 0:
        return 0.0
    return monto * (tasa_anual / 100) * (meses / 12)

def actualizar_saldo(saldo_actual, monto_transaccion, es_ingreso=True):
    if es_ingreso:
        return saldo_actual + monto_transaccion
    return saldo_actual - monto_transaccion

def generar_id():
    return random.randint(100000, 999999)


# --- Validaciones puras (para usar en APIs o formularios) ---

def validar_correo(correo):
    patron = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(patron, str(correo)))

def validar_telefono(telefono):
    # Número de celular a 10 dígitos
    patron = r'^\d{10}$'
    return bool(re.match(patron, str(telefono)))

def validar_fecha(fecha_texto):
    try:
        datetime.strptime(fecha_texto, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validar_tipo_movimiento(tipo):
    tipo_limpio = str(tipo).strip().capitalize()
    return tipo_limpio in ("Ingreso", "Retiro")


# --- Capturas por terminal con control de flujo (sin break/continue) ---

def solicitar_id(mensaje):
    valido = False
    valor_id = 0
    
    while not valido:
        entrada = input(mensaje)
        try:
            valor_id = int(entrada)
            if valor_id > 0:
                valido = True
            else:
                print("El ID debe ser mayor a 0.")
        except ValueError:
            print("Error: Ingresa un número entero válido.")
            
    return valor_id

def solicitar_monto(mensaje):
    valido = False
    valor_monto = 0.0
    
    while not valido:
        entrada = input(mensaje)
        try:
            valor_monto = float(entrada)
            if valor_monto >= 0:
                valido = True
            else:
                print("El monto no puede ser negativo.")
        except ValueError:
            print("Error: Usa solo números y punto decimal.")
            
    return valor_monto

def solicitar_fecha(mensaje):
    valido = False
    fecha_formateada = ""
    
    while not valido:
        entrada = input(mensaje)
        try:
            objeto_fecha = datetime.strptime(entrada, "%Y-%m-%d")
            fecha_formateada = objeto_fecha.strftime("%Y-%m-%d")
            valido = True
        except ValueError:
            print("Fecha inválida. Usa el formato AAAA-MM-DD.")
            
    return fecha_formateada

def solicitar_tipo_movimiento(mensaje):
    valido = False
    tipo_movimiento = ""
    
    while not valido:
        entrada = input(mensaje)
        texto_limpio = entrada.strip().capitalize()
        
        if texto_limpio in ("Ingreso", "Retiro"):
            tipo_movimiento = texto_limpio
            valido = True
        else:
            print("Opción inválida. Debe ser 'Ingreso' o 'Retiro'.")
            
    return tipo_movimiento