# Control de Ahorro Personal

# Link de github:  https://github.com/valentina7730/Contro-Ahorro-Personal.git
# link de Google Drive:  https://github.com/valentina7730/Contro-Ahorro-Personal.git

Proyecto de Programación V (CIAF). Endpoints en Python por consola que trabajan sobre una base de datos MySQL de ahorro personal.

## Estructura

```
Contro Ahorro Personal/
├── .env                      # datos de conexion (NO se sube a GitHub)
├── db_connection.py          # unico archivo que habla con MySQL
├── requirements.txt
├── validaciones/
│   └── libreria_ahorro.py    # libreria propia: validaciones y calculos
├── endpoints/
│   └── movimientos/
│       ├── movimientos_comun.py                     # consulta por id + regla del saldo
│       ├── endpoint_GET_listarMovimientos.py
│       ├── endpoint_POST_nuevoMovimiento.py
│       ├── endpoint_PUT_actualizaMovimiento.py
│       ├── endpoint_PATCH_actualizaMontoMovimiento.py
│       └── endpoint_DELETE_borrarMovimiento.py
└── sql/
    ├── creacion_schema.sql   # 1) tablas, reglas CHECK y vistas
    ├── creacion_usuario.sql  # 2) usuario ahorro_app con permisos minimos
    └── datos_prueba.sql      # 3) datos para probar
```

## Cómo ejecutarlo

1. En MySQL Workbench, con root, ejecutar en orden: `creacion_schema.sql`, `creacion_usuario.sql` y `datos_prueba.sql`.
2. Crear el archivo `.env` en la raíz:
   ```
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=ahorro_app
   DB_PASSWORD=12345678
   DB_NAME=ahorroapp
   ```
3. Instalar dependencias:
   ```
   python -m venv venv
   source venv/bin/activate        # en Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. Probar la conexión: `python db_connection.py`
5. Ejecutar un endpoint con el botón **Run** de VS Code, o desde la terminal:
   ```
   python endpoints/movimientos/endpoint_GET_listarMovimientos.py
   ```
