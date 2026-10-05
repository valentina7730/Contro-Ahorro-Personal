import json
from db_connection import ejecutar_consulta, ErrorBaseDatos

def get_all_movements(limit=50, offset=0):
    """Reads movements ordered by id, with a limit so it never loads the whole table."""
    sql = """
        SELECT
            idMovimiento,
            idCuenta,
            tipo,
            monto,
            fechaMovimiento,
            descripcion
        FROM movimientos
        ORDER BY idMovimiento ASC
        LIMIT %s OFFSET %s
    """
    return ejecutar_consulta(sql, (limit, offset))


def run_get():
    try:
        movements = get_all_movements()
        print(json.dumps(movements, indent=2, ensure_ascii=False))
    except ErrorBaseDatos as error:
        print("Database error: " + error.mensaje)
    except Exception:
        print("Unexpected error. Contact the administrator.")


if __name__ == "__main__":
    run_get()