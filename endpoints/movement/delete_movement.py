import json

from db_connection import ejecutar_consulta, ejecutar_comando, ErrorBaseDatos
from validation.id_validator import ask_id


def get_movement_by_id(movement_id):
    """Returns the movement as a dictionary, or None if it does not exist."""
    sql = """
        SELECT
            idMovimiento,
            idCuenta,
            tipo,
            monto,
            fechaMovimiento,
            descripcion
        FROM movimientos
        WHERE idMovimiento = %s
    """
    return ejecutar_consulta(sql, (movement_id,), una_fila=True)


def delete_movement(movement_id):
    """Deletes the movement by its primary key."""
    sql = "DELETE FROM movimientos WHERE idMovimiento = %s"
    return ejecutar_comando(sql, (movement_id,))


def run_delete():
    try:
        movement_id = ask_id("Movement ID to delete: ")

        movement = get_movement_by_id(movement_id)
        if movement is None:
            print(json.dumps(None, indent=2))
            return

        delete_movement(movement_id)
        print(json.dumps({"deleted_idMovimiento": movement_id}, indent=2))
    except ErrorBaseDatos as error:
        print("Database error: " + error.mensaje)
    except Exception:
        print("Unexpected error. Contact the administrator.")


if __name__ == "__main__":
    run_delete()