import json

from db_connection import ejecutar_consulta, ejecutar_comando, ErrorBaseDatos
from validation.id_validator import ask_id
from validation.amount_validator import ask_amount
from validation.date_validator import ask_date
from validation.type_validator import ask_movement_type


def capture_data():
    """Asks for all the data of the new movement."""
    account_id = ask_id("Account ID: ")
    movement_type = ask_movement_type("Type (Ingreso/Retiro): ")
    amount = ask_amount("Amount: ")
    movement_date = ask_date("Date (YYYY-MM-DD): ")
    description = input("Description: ")
    return {
        "idCuenta": account_id,
        "tipo": movement_type,
        "monto": amount,
        "fechaMovimiento": movement_date.date(),  # datetime -> only the date
        "descripcion": description,
    }


def insert_movement(data):
    """Inserts the movement. Returns the result with the new id (ultimoId)."""
    sql = """
        INSERT INTO movimientos
            (idCuenta, tipo, monto, fechaMovimiento, descripcion)
        VALUES (%s, %s, %s, %s, %s)
    """
    parameters = (
        data["idCuenta"],
        data["tipo"],
        data["monto"],
        data["fechaMovimiento"],
        data["descripcion"],
    )
    return ejecutar_comando(sql, parameters)


def get_movement_by_id(movement_id):
    """Returns the movement as a dictionary, or None if it does not exist."""
    sql = """
        SELECT idMovimiento, idCuenta, tipo, monto, fechaMovimiento, descripcion
        FROM movimientos
        WHERE idMovimiento = %s
    """
    return ejecutar_consulta(sql, (movement_id,), una_fila=True)


def run_post():
    try:
        data = capture_data()

        result = insert_movement(data)
        new_id = result["ultimoId"]

        created = get_movement_by_id(new_id)
        print(json.dumps(created, indent=2, ensure_ascii=False))
    except ErrorBaseDatos as error:
        print("Database error: " + error.mensaje)
    except Exception:
        print("Unexpected error. Contact the administrator.")


if __name__ == "__main__":
    run_post()