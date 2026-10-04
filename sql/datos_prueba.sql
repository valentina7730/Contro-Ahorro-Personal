-- =====================================================================
-- DATOS DE PRUEBA (opcional). Ejecutar después de creacion_schema.sql
-- Los saldos y montos de metas ya cuadran con los movimientos insertados.
-- Password de todos los usuarios: 123456 (guardado como SHA-256;
-- en Python: hashlib.sha256("123456".encode()).hexdigest())
-- =====================================================================
USE `ahorroapp`;

INSERT INTO usuarios (idUsuario, tipoDocumento, numeroDocumento, nombre, correo, telefono, password) VALUES
(1, 'CC', '1088123456', 'Laura Gomez',      'laura.gomez@mail.com',    '3101234567', SHA2('123456', 256)),
(2, 'CC', '1093456789', 'Andres Rios',      'andres.rios@mail.com',    '3159876543', SHA2('123456', 256)),
(3, 'CE', '987654',     'Valentina Mejia',  'valentina.mejia@mail.com','3204567890', SHA2('123456', 256));

INSERT INTO asesores (idAsesor, numeroDocumento, nombre, correo, telefono) VALUES
(1, '10045678', 'Carlos Ospina',  'carlos.ospina@ahorro.com',  '3001112233'),
(2, '42123987', 'Diana Cardona',  'diana.cardona@ahorro.com',  '3014445566');

-- saldoActual = saldoInicial + ingresos + intereses - retiros -/+ transferencias
INSERT INTO cuentas (idCuenta, idUsuario, saldoInicial, saldoActual, tasaInteresMensual, fechaApertura, estado) VALUES
(1, 1,  500000.00,  902500.00, 0.50, '2026-09-01', 'Activa'),
(2, 1,       0.00,  500000.00, 0.80, '2026-09-15', 'Activa'),
(3, 2, 1000000.00, 1630000.00, 0.50, '2026-09-01', 'Activa'),
(4, 3,  200000.00,  170000.00, 0.50, '2026-09-10', 'Activa');

INSERT INTO categorias (idCategoria, idUsuario, nombre, presupuestoMensual) VALUES
(1, 1, 'Alimentacion', 600000.00),
(2, 1, 'Transporte',   200000.00),
(3, 2, 'Vivienda',     800000.00),
(4, 2, 'Alimentacion', 500000.00),
(5, 3, 'Transporte',   150000.00);

INSERT INTO metas (idMeta, idUsuario, nombre, montoObjetivo, montoActual, fechaLimite, estado) VALUES
(1, 1, 'Viaje a Cartagena',   2000000.00,  800000.00, '2026-12-15', 'EnProgreso'),
(2, 1, 'Fondo de emergencia', 3000000.00,  300000.00, '2027-06-30', 'EnProgreso'),
(3, 2, 'Portatil nuevo',      1500000.00, 1500000.00, '2026-11-30', 'Cumplida'),
(4, 3, 'Curso de ingles',      400000.00,  150000.00, '2026-10-31', 'EnProgreso');

INSERT INTO movimientos (idMovimiento, idCuenta, tipo, monto, fechaMovimiento, descripcion, idMeta, idCategoria, idCuentaDestino) VALUES
-- Cuenta 1 (Laura)
(1,  1, 'Ingreso',        800000.00, '2026-09-05', 'Salario quincena',            1,    NULL, NULL),
(2,  1, 'Retiro',         150000.00, '2026-09-10', 'Mercado',                     NULL, 1,    NULL),
(3,  1, 'Transferencia',  200000.00, '2026-09-20', 'Paso a cuenta de emergencia', NULL, NULL, 2),
(4,  1, 'Interes',          2500.00, '2026-09-30', 'Interes septiembre',          NULL, NULL, NULL),
(5,  1, 'Retiro',          50000.00, '2026-10-02', 'Pasajes bus',                 NULL, 2,    NULL),
-- Cuenta 2 (Laura)
(6,  2, 'Ingreso',        300000.00, '2026-10-01', 'Ahorro para emergencias',     2,    NULL, NULL),
-- Cuenta 3 (Andres) -> la meta 3 queda Cumplida
(7,  3, 'Ingreso',       1500000.00, '2026-09-15', 'Prima',                       3,    NULL, NULL),
(8,  3, 'Retiro',         750000.00, '2026-10-01', 'Arriendo',                    NULL, 3,    NULL),
(9,  3, 'Retiro',         120000.00, '2026-10-03', 'Mercado',                     NULL, 4,    NULL),
-- Cuenta 4 (Valentina) -> excede el presupuesto de Transporte (150.000)
(10, 4, 'Ingreso',        150000.00, '2026-09-25', 'Ahorro curso',                4,    NULL, NULL),
(11, 4, 'Retiro',         180000.00, '2026-10-02', 'Gasolina y mantenimiento',    NULL, 5,    NULL);

INSERT INTO asesorias (idAsesoria, idAsesor, idUsuario, fechaAsesoria, observaciones) VALUES
(1, 1, 1, '2026-09-28', 'Buen ritmo de ahorro. Se recomienda aumentar el aporte mensual a la meta del viaje.'),
(2, 2, 3, '2026-10-03', 'Excedio el presupuesto de transporte. Revisar gastos de la moto.');
