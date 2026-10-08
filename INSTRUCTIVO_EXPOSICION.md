# Instructivo para la exposición – Control de Ahorro Personal

Este documento es para nosotros (el equipo): dice **dónde está cada cosa del requerimiento** y **cómo explicarla** en la exposición.

> Ojo: el mapa de requerimientos se armó con los códigos AHO que están en los comentarios de `sql/creacion_schema.sql`. Antes de exponer, revisarlo contra el documento oficial REQUERIMIENTOS_09 por si algún código dice otra cosa.

---

## 1. Cómo está organizado el proyecto (explicarlo en 1 minuto)

El proyecto está dividido en **capas**. Cada capa tiene una sola responsabilidad:

| Capa | Archivo | Qué hace |
|---|---|---|
| 1. Configuración | `.env` | Guarda host, puerto, usuario, password y nombre de la BD. No se sube a GitHub. |
| 2. Conexión | `db_connection.py` | Es el **único** archivo que abre conexiones a MySQL. Lee el `.env`, ejecuta el SQL y traduce los errores a español. |
| 3. Reglas del negocio | `validaciones/libreria_ahorro.py` y `endpoints/movimientos/movimientos_comun.py` | Validaciones de los datos que escribe el usuario, cálculo de intereses y la regla del saldo. |
| 4. Endpoints | `endpoints/movimientos/endpoint_*.py` | Uno por cada verbo HTTP (GET, POST, PUT, PATCH, DELETE). Piden datos, llaman a las capas de abajo e imprimen JSON. |
| Base de datos | `sql/*.sql` | Tablas, reglas CHECK, llaves foráneas, vistas, usuario y datos de prueba. |

**Frase para decir:** *"Separamos el proyecto en capas para que si mañana cambia la base de datos, solo se toque `db_connection.py`, y si cambia una regla del negocio, solo se toque la librería."*

---

## 2. Mapa: requerimiento → dónde está en el código

Leyenda: ✅ hecho en Python · 🗄️ hecho en la base de datos (tabla, regla o vista) · ⏳ pendiente

### Base de datos y conexión

| Qué se pide | Dónde está | Estado |
|---|---|---|
| Modelo de base de datos | `sql/creacion_schema.sql` – 7 tablas: usuarios, asesores, cuentas, categorias, metas, movimientos, asesorias | 🗄️ |
| Reglas de integridad | Mismo archivo: `CHECK` (saldo >= 0, monto > 0, documento de 6 a 12 dígitos, teléfono de 10) y `FOREIGN KEY` | 🗄️ |
| Usuario de la aplicación (no usar root) – entregable 2.d | `sql/creacion_usuario.sql` – usuario `ahorro_app` solo con SELECT, INSERT, UPDATE, DELETE | 🗄️ |
| Datos de prueba | `sql/datos_prueba.sql` – los saldos ya cuadran con los movimientos | 🗄️ |
| Conexión con variables de entorno | `db_connection.py` → `cargar_configuracion()` y `obtener_conexion()` | ✅ |
| Evitar inyección SQL | `db_connection.py` – siempre `%s` con los valores aparte (ver comentario BIEN/MAL al inicio) | ✅ |
| Manejo de errores | `db_connection.py` → clase `ErrorBaseDatos` y diccionario `MENSAJES_ERROR_MYSQL`. En los endpoints, `try/except` | ✅ |
| Transacciones | `db_connection.py` → `ejecutar_transaccion()` | ✅ |

### Requerimientos funcionales (AHO)

| Código | Qué es | Dónde está | Estado |
|---|---|---|---|
| AHO-0002 | Usuarios (ahorradores) | Tabla `usuarios`. Validaciones listas en `libreria_ahorro.py`: `validar_documento`, `validar_correo`, `validar_telefono` | 🗄️ ✅ validaciones · ⏳ endpoints |
| AHO-0003 | Cuentas de ahorro | Tabla `cuentas`. En Python: `validar_datos_contra_bd()` revisa que la cuenta exista y esté Activa | 🗄️ ✅ parcial |
| AHO-0004 | Registrar ingresos y retiros | `endpoint_POST_nuevoMovimiento.py`. El saldo se actualiza en la misma transacción (`movimientos_comun.py`) | ✅ |
| AHO-0005 | Metas de ahorro | Tabla `metas` | 🗄️ · ⏳ endpoints |
| AHO-0006 | Ingreso que aporta a una meta | En POST y PUT se pide `idMeta`. `SQL_ACTUALIZAR_META` en `movimientos_comun.py` suma el avance y pone la meta en **Cumplida** cuando llega al objetivo | ✅ |
| AHO-0007 | Categorías de gasto y presupuesto | En un Retiro se pide `idCategoria`. Vista `vw_presupuesto_categorias_mes` (gastado vs. presupuesto) | ✅ 🗄️ |
| AHO-0008 | Asesores y asesorías | Tablas `asesores` y `asesorias` | 🗄️ · ⏳ endpoints |
| AHO-0009 | Consultar movimientos | `endpoint_GET_listarMovimientos.py` | ✅ |
| AHO-0010 | Reporte de saldo, ingresos y retiros por usuario | Vista `vw_reporte_saldo_usuario` | 🗄️ · ⏳ reporte en Python con for/if |
| AHO-0011 | Cumplimiento de metas (% de avance) | Vista `vw_cumplimiento_metas` | 🗄️ · ⏳ reporte en Python con for/if |
| AHO-0016 | Intereses | Columna `tasaInteresMensual`, tipo de movimiento `Interes` y función `calcular_interes()` en la librería | 🗄️ ✅ cálculo · ⏳ proceso que lo genere |

### CRUD de movimientos (lo que se va a mostrar en vivo)

| Verbo | Archivo | Qué hace con el saldo |
|---|---|---|
| GET | `endpoint_GET_listarMovimientos.py` | Nada, solo lee (con LIMIT para no traer toda la tabla) |
| POST | `endpoint_POST_nuevoMovimiento.py` | Ingreso suma, Retiro resta. Si tiene meta, suma a la meta |
| PUT | `endpoint_PUT_actualizaMovimiento.py` | Deshace el movimiento viejo y aplica el nuevo |
| PATCH | `endpoint_PATCH_actualizaMontoMovimiento.py` | Aplica solo la diferencia entre el monto nuevo y el viejo |
| DELETE | `endpoint_DELETE_borrarMovimiento.py` | Devuelve el saldo a como estaba antes del movimiento |

---

## 3. Lo más importante para explicar: la regla del saldo

Está en `endpoints/movimientos/movimientos_comun.py`, función `preparar_operaciones_de_saldo(anterior, nuevo)`.

**Problema:** si se registra un retiro pero no se descuenta de la cuenta, el saldo queda mal. Y si se descuenta en un paso aparte y ese paso falla, queda el movimiento guardado sin el descuento.

**Solución:** cada endpoint arma una lista de sentencias y las manda juntas a `ejecutar_transaccion()`. Si una falla se hace **rollback** y no queda nada guardado.

```
cambio en el saldo = efecto del movimiento NUEVO − efecto del movimiento ANTERIOR

POST   → anterior = None   (solo se aplica el nuevo)
DELETE → nuevo = None      (solo se deshace el anterior)
PUT    → los dos
PATCH  → los dos (el nuevo es igual al anterior pero con otro monto)
```

Con esa sola función se resuelven los 4 endpoints, sin repetir código.

Además, antes de guardar se revisa que ninguna cuenta quede con saldo negativo (`_validar_saldo_suficiente`). La tabla también tiene `CHECK (saldoActual >= 0)` como segunda protección.

**Frase para decir:** *"Validamos en dos niveles: en Python, para darle al usuario un mensaje claro, y en la base de datos con CHECK, por si algún día alguien inserta datos sin pasar por el programa."*

---

## 4. Guion de la exposición (unos 15 minutos)

Repártanlo entre los integrantes. Sugerencia:

| Parte | Tiempo | Quién | Qué mostrar |
|---|---|---|---|
| 1. Problema y modelo de datos | 3 min | Integrante 1 | Abrir `creacion_schema.sql`: tablas, CHECK, llaves foráneas. Mostrar el diagrama en Workbench si lo tienen |
| 2. Usuario y seguridad | 2 min | Integrante 1 | `creacion_usuario.sql`: por qué no se usa root y por qué solo tiene esos 4 permisos. Mostrar `.env` y `.gitignore` |
| 3. Capa de conexión | 3 min | Integrante 2 | `db_connection.py`: `%s` contra inyección SQL, `ErrorBaseDatos`, `ejecutar_transaccion`. Ejecutar `python db_connection.py` |
| 4. Librería de validaciones | 2 min | Integrante 3 | `libreria_ahorro.py`: los `solicitar_*` repiten con `while not valido` (sin break). Mostrar un caso con un dato malo |
| 5. Demo de los endpoints | 5 min | Integrante 2 y 3 | Seguir la demo del punto 5 |

---

## 5. Demo en vivo (paso a paso, ya probada)

Antes de empezar, ejecutar en Workbench (con root) `creacion_schema.sql` y luego `datos_prueba.sql` para tener la base limpia. Así los ids vuelven a empezar y el movimiento nuevo será el **12**. Tener abierta en Workbench esta consulta para mostrar cómo cambia el saldo:

```sql
SELECT idCuenta, saldoActual FROM cuentas WHERE idCuenta = 4;
SELECT idMeta, montoActual, estado FROM metas WHERE idMeta = 4;
```

Al inicio: **cuenta 4 = 170.000** y **meta 4 = 150.000 (EnProgreso)**.

**Paso 1 – GET.** Ejecutar `endpoint_GET_listarMovimientos.py`. Salen los 11 movimientos de prueba.

**Paso 2 – Validaciones.** Ejecutar `endpoint_POST_nuevoMovimiento.py` y escribir datos malos a propósito:
- idCuenta: `abc` → pide de nuevo
- Monto: `-5` → "El monto debe ser mayor a 0"
- Fecha: `2026-02-30` → "Fecha invalida"

**Paso 3 – POST de un ingreso que completa una meta.**
```
idCuenta: 4
Tipo: ingreso          (en minúscula, se corrige solo)
Monto: 250000
Fecha: 2026-10-08
Descripcion: Aporte curso
idMeta: 4
```
Resultado en Workbench: **cuenta 4 = 420.000** y **meta 4 = 400.000, estado Cumplida**.

**Paso 4 – Saldo insuficiente.** POST con cuenta `4`, `Retiro`, monto `999999`.
→ "Saldo insuficiente en la cuenta 4…" y no se guarda nada.

**Paso 5 – Meta de otra persona.** POST con cuenta `4`, `Ingreso`, monto `100`, idMeta `1`.
→ "La meta no pertenece al dueño de la cuenta."

**Paso 6 – PATCH.** Cambiar el monto del movimiento creado en el paso 3 (el `idMovimiento` que imprimió el POST; con la base limpia es el 12) a `200000`.
→ cuenta 4 = **370.000**, meta 4 = **350.000** y vuelve a **EnProgreso**.

**Paso 7 – PUT sobre una transferencia.** PUT con idMovimiento `3`.
→ "El movimiento 3 es de tipo Transferencia y no se puede reemplazar."

**Paso 8 – DELETE.** Borrar el movimiento 12.
→ cuenta 4 vuelve a **170.000** y meta 4 a **150.000**. Todo queda como al inicio.

**Paso 9 – DELETE de algo que no existe.** idMovimiento `999` → imprime `null`.

---

## 6. Preguntas que puede hacer el profesor

**¿Por qué usan transacciones?**
Porque un movimiento cambia hasta 3 tablas (movimientos, cuentas, metas). Si se guarda una y falla otra, los datos quedan inconsistentes. Con la transacción se guarda todo o nada.

**¿Cuál es la diferencia entre PUT y PATCH?**
PUT reemplaza todo el movimiento (cuenta, tipo, monto, fecha, descripción). PATCH cambia solo el monto.

**¿Qué es idempotencia? ¿Cuáles son idempotentes?**
Es que repetir la misma petición deja el mismo resultado. GET, PUT y DELETE lo son: repetir un PUT con los mismos datos deja el saldo igual. POST no: dos POST crean dos movimientos y mueven el saldo dos veces.

**¿Cómo evitan la inyección SQL?**
Nunca se arma el SQL pegando texto. Siempre se usa `%s` y los valores van aparte; el conector los escapa.

**¿Por qué no se conectan con root?**
Por el principio de mínimo privilegio. Si alguien roba la clave de `ahorro_app`, no puede borrar tablas ni crear usuarios.

**¿Por qué usan Decimal para el saldo?**
Porque es dinero. Con float, `0.1 + 0.2` no da exactamente `0.3`. En la base el campo es `decimal(15,2)`.

**¿Por qué validan en Python si la base ya tiene CHECK?**
Python da mensajes claros al usuario y la base es la última protección. Si solo validara la base, el usuario vería un error técnico.

**¿Por qué no se pueden editar transferencias ni intereses con PUT?**
Porque esos los genera el sistema (una transferencia mueve dos cuentas y el interés lo calcula el banco). Si se editaran a mano, se podría romper la regla de la tabla que exige `idCuentaDestino` en las transferencias.

**¿Por qué se quitó la función `generar_id()` con random?**
Las tablas ya usan `AUTO_INCREMENT`. Un id aleatorio podía repetirse con uno existente y dar error de llave duplicada.

**¿Qué hace la línea `sys.path.append(...)` al inicio de cada endpoint?**
Agrega la carpeta raíz del proyecto para que Python encuentre `db_connection.py` y la librería al ejecutar el archivo con el botón Run de VS Code, aunque el endpoint esté en una subcarpeta.

**¿Cómo se calcula el interés?**
`calcular_interes(saldo, tasa_mensual, meses)` usa interés simple: saldo × tasa / 100 × meses. Con los datos de prueba: 500.000 al 0,5 % por 1 mes = 2.500, que es el movimiento 4 de tipo Interés.

---

## 7. Qué se cambió en la reorganización (para que todo el equipo lo sepa)

- Se pasó todo a español para que quede igual que la práctica de clase (`endpoint_VERBO_nombre.py`).
- `validation/` ahora es `validaciones/`. Se borraron `amount_validator.py`, `date_validator.py`, `id_validator.py` y `type_validator.py`, porque hacían lo mismo que `libreria_ahorro.py` pero con menos validaciones (aceptaban montos negativos y ids en 0).
- **Corrección importante:** antes los endpoints guardaban el movimiento pero **no actualizaban el saldo de la cuenta ni el avance de la meta**. Ahora sí, dentro de una transacción.
- POST y PUT piden `idMeta` (en ingresos) o `idCategoria` (en retiros), que son opcionales.
- La descripción vacía se guarda como NULL y se valida que no pase de 200 caracteres.
- `calcular_interes` ahora usa la tasa **mensual**, que es la que tiene la tabla `cuentas` (antes usaba anual y daba 12 veces menos).
- Se quitó `generar_id()` (ver la pregunta de arriba).
- Los endpoints se pueden ejecutar con el botón Run de VS Code (antes daba `ModuleNotFoundError`).
