import json

from db_connection import ejecutar_consulta, ejecutar_comando, ErrorBaseDatos
from validation.id_validator import ask_id
from validation.amount_validator import ask_amount
from validation.date_validator import ask_date
from validation.type_validator import ask_movement_type


def capture_data():
    """Asks for the movement id and ALL the new values."""
    movement_id = ask_id("Movement ID to replace: ")
    account_id = ask_id("New account ID: ")
    movement_type = ask_movement_type("New type (Ingreso/Retiro): ")
    amount = ask_amount("New amount: ")
    movement_date = ask_date("New date (YYYY-MM-DD): ")
    description = input("New description: ")
    return {
        "idMovimiento": movement_id,
        "idCuenta": account_id,
        "tipo": movement_type,
        "monto": amount,
        "fechaMovimiento": movement_date.date(),  # datetime -> only the date
        "descripcion": description,
    }


def get_movement_by_id(movement_id):
    """Returns the movement as a dictionary, or None if it does not exist."""
    sql = """
        SELECT idMovimiento, idCuenta, tipo, monto, fechaMovimiento, descripcion
        FROM movimientos
        WHERE idMovimiento = %s
    """
    return ejecutar_consulta(sql, (movement_id,), una_fila=True)


def update_movement(data):
    """Replaces every column. The id goes LAST because it is used in the WHERE."""
    sql = """
        UPDATE movimientos
        SET
            idCuenta = %s,
            tipo = %s,
            monto = %s,
            fechaMovimiento = %s,
            descripcion = %s
        WHERE idMovimiento = %s
    """
    parameters = (
        data["idCuenta"],
        data["tipo"],
        data["monto"],
        data["fechaMovimiento"],
        data["descripcion"],
        data["idMovimiento"],
    )
    return ejecutar_comando(sql, parameters)


def run_put():
    try:
        data = capture_data()

        movement = get_movement_by_id(data["idMovimiento"])
        if movement is None:
            print(json.dumps(None, indent=2))
            return

        update_movement(data)

        updated = get_movement_by_id(data["idMovimiento"])
        print(json.dumps(updated, indent=2, ensure_ascii=False))
    except ErrorBaseDatos as error:
        print("Database error: " + error.mensaje)
    except Exception:
        print("Unexpected error. Contact the administrator.")


if __name__ == "__main__":
    run_put()