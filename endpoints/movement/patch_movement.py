import json

from db_connection import ejecutar_consulta, ejecutar_comando, ErrorBaseDatos
from validation.id_validator import ask_id
from validation.amount_validator import ask_amount


def capture_data():
    """Asks for the movement id and the new amount."""
    movement_id = ask_id("Movement ID to update: ")
    amount = ask_amount("New amount: ")
    return {"idMovimiento": movement_id, "monto": amount}


def get_movement_by_id(movement_id):
    """Returns the movement as a dictionary, or None if it does not exist."""
    sql = """
        SELECT idMovimiento, idCuenta, tipo, monto, fechaMovimiento, descripcion
        FROM movimientos
        WHERE idMovimiento = %s
    """
    return ejecutar_consulta(sql, (movement_id,), una_fila=True)


def update_amount(movement_id, amount):
    """Changes ONLY the amount column."""
    sql = """
        UPDATE movimientos
        SET monto = %s
        WHERE idMovimiento = %s
    """
    return ejecutar_comando(sql, (amount, movement_id))


def run_patch():
    try:
        data = capture_data()

        movement = get_movement_by_id(data["idMovimiento"])
        if movement is None:
            print(json.dumps(None, indent=2))
            return

        update_amount(data["idMovimiento"], data["monto"])

        output = {
            "idMovimiento": data["idMovimiento"],
            "new_amount": data["monto"],
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    except ErrorBaseDatos as error:
        print("Database error: " + error.mensaje)
    except Exception:
        print("Unexpected error. Contact the administrator.")


if __name__ == "__main__":
    run_patch()