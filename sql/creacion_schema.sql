-- =====================================================================
-- PROYECTO: Control de Ahorro Personal (REQUERIMIENTOS_09)
-- MOTOR:    MySQL 8.0.16 o superior (necesario para que los CHECK se apliquen)
-- ORDEN DE EJECUCIÓN:
--   1) creacion_schema.sql   (este archivo, con root o un usuario admin)
--   2) creacion_usuario.sql  (crea el usuario de la aplicación)
--   3) datos_prueba.sql      (opcional, datos para probar)
-- =====================================================================

CREATE DATABASE IF NOT EXISTS `ahorroapp`
  DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;
USE `ahorroapp`;

-- Se borran en orden inverso a las dependencias (hijas primero)
DROP VIEW  IF EXISTS `vw_presupuesto_categorias_mes`;
DROP VIEW  IF EXISTS `vw_cumplimiento_metas`;
DROP VIEW  IF EXISTS `vw_reporte_saldo_usuario`;
DROP TABLE IF EXISTS `asesorias`;
DROP TABLE IF EXISTS `movimientos`;
DROP TABLE IF EXISTS `metas`;
DROP TABLE IF EXISTS `categorias`;
DROP TABLE IF EXISTS `cuentas`;
DROP TABLE IF EXISTS `asesores`;
DROP TABLE IF EXISTS `usuarios`;

-- ---------------------------------------------------------------------
-- 1. USUARIOS (ahorradores)                         -> AHO-0002
-- ---------------------------------------------------------------------
CREATE TABLE `usuarios` (
  `idUsuario`         int NOT NULL AUTO_INCREMENT,
  `tipoDocumento`     enum('CC','TI','CE','PAS') NOT NULL,
  `numeroDocumento`   varchar(12)  NOT NULL,              -- 6 a 12 dígitos
  `nombre`            varchar(60)  NOT NULL,              -- solo letras, mín 3
  `correo`            varchar(70)  NOT NULL,
  `telefono`          varchar(10)  NOT NULL,              -- 10 dígitos
  `password`          varchar(255) NOT NULL,              -- guardar HASH, no texto plano
  `fechaCreacion`     timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fechaModificacion` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`idUsuario`),
  UNIQUE KEY `uk_usuarios_documento` (`numeroDocumento`),
  UNIQUE KEY `uk_usuarios_correo` (`correo`),
  CONSTRAINT `chk_usuarios_documento` CHECK (`numeroDocumento` REGEXP '^[0-9]{6,12}$'),
  CONSTRAINT `chk_usuarios_nombre`    CHECK (CHAR_LENGTH(`nombre`) >= 3),
  CONSTRAINT `chk_usuarios_telefono`  CHECK (`telefono` REGEXP '^[0-9]{10}$')
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------
-- 2. ASESORES                                        -> AHO-0008
-- ---------------------------------------------------------------------
CREATE TABLE `asesores` (
  `idAsesor`          int NOT NULL AUTO_INCREMENT,
  `numeroDocumento`   varchar(12) NOT NULL,
  `nombre`            varchar(60) NOT NULL,
  `correo`            varchar(70) NOT NULL,
  `telefono`          varchar(10) NOT NULL,
  `fechaCreacion`     timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fechaModificacion` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`idAsesor`),
  UNIQUE KEY `uk_asesores_documento` (`numeroDocumento`),
  CONSTRAINT `chk_asesores_documento` CHECK (`numeroDocumento` REGEXP '^[0-9]{6,12}$'),
  CONSTRAINT `chk_asesores_telefono`  CHECK (`telefono` REGEXP '^[0-9]{10}$')
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------
-- 3. CUENTAS DE AHORRO                     -> AHO-0003, AHO-0016
-- ---------------------------------------------------------------------
CREATE TABLE `cuentas` (
  `idCuenta`           int NOT NULL AUTO_INCREMENT,
  `idUsuario`          int NOT NULL,
  `saldoInicial`       decimal(15,2) NOT NULL DEFAULT 0.00,
  `saldoActual`        decimal(15,2) NOT NULL DEFAULT 0.00,
  `tasaInteresMensual` decimal(5,2)  NOT NULL DEFAULT 0.50,   -- % mensual configurable
  `fechaApertura`      date NOT NULL,
  `estado`             enum('Activa','Inactiva') NOT NULL DEFAULT 'Activa',
  `fechaCreacion`      timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fechaModificacion`  timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`idCuenta`),
  KEY `idx_cuentas_usuario` (`idUsuario`),
  CONSTRAINT `fk_cuentas_usuario` FOREIGN KEY (`idUsuario`) REFERENCES `usuarios` (`idUsuario`),
  CONSTRAINT `chk_cuentas_saldo_inicial` CHECK (`saldoInicial` >= 0),
  CONSTRAINT `chk_cuentas_saldo_actual`  CHECK (`saldoActual`  >= 0),
  CONSTRAINT `chk_cuentas_tasa`          CHECK (`tasaInteresMensual` >= 0 AND `tasaInteresMensual` <= 100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------
-- 4. CATEGORÍAS DE GASTO (cada ahorrador tiene las suyas) -> AHO-0007
-- ---------------------------------------------------------------------
CREATE TABLE `categorias` (
  `idCategoria`        int NOT NULL AUTO_INCREMENT,
  `idUsuario`          int NOT NULL,
  `nombre`             varchar(40) NOT NULL,
  `presupuestoMensual` decimal(15,2) NOT NULL DEFAULT 0.00,
  `fechaCreacion`      timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fechaModificacion`  timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`idCategoria`),
  UNIQUE KEY `uk_categorias_usuario_nombre` (`idUsuario`, `nombre`),
  CONSTRAINT `fk_categorias_usuario` FOREIGN KEY (`idUsuario`) REFERENCES `usuarios` (`idUsuario`),
  CONSTRAINT `chk_categorias_presupuesto` CHECK (`presupuestoMensual` >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------
-- 5. METAS DE AHORRO                              -> AHO-0005, AHO-0006
-- ---------------------------------------------------------------------
CREATE TABLE `metas` (
  `idMeta`            int NOT NULL AUTO_INCREMENT,
  `idUsuario`         int NOT NULL,
  `nombre`            varchar(60) NOT NULL,
  `montoObjetivo`     decimal(15,2) NOT NULL,
  `montoActual`       decimal(15,2) NOT NULL DEFAULT 0.00,
  `fechaLimite`       date NOT NULL,
  `estado`            enum('EnProgreso','Cumplida','Vencida') NOT NULL DEFAULT 'EnProgreso',
  `fechaCreacion`     timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fechaModificacion` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`idMeta`),
  KEY `idx_metas_usuario` (`idUsuario`),
  CONSTRAINT `fk_metas_usuario` FOREIGN KEY (`idUsuario`) REFERENCES `usuarios` (`idUsuario`),
  CONSTRAINT `chk_metas_objetivo` CHECK (`montoObjetivo` > 0),
  CONSTRAINT `chk_metas_actual`   CHECK (`montoActual` >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------
-- 6. MOVIMIENTOS                       -> AHO-0004, AHO-0006, AHO-0007, AHO-0009
--    tipo:
--      Ingreso       -> puede asociarse a una meta (idMeta)
--      Retiro        -> es un gasto, puede asociarse a una categoría (idCategoria)
--      Transferencia -> requiere idCuentaDestino
--      Interes       -> lo genera el sistema (AHO-0016)
-- ---------------------------------------------------------------------
CREATE TABLE `movimientos` (
  `idMovimiento`      int NOT NULL AUTO_INCREMENT,
  `idCuenta`          int NOT NULL,
  `tipo`              enum('Ingreso','Retiro','Transferencia','Interes') NOT NULL,
  `monto`             decimal(15,2) NOT NULL,
  `fechaMovimiento`   date NOT NULL,
  `descripcion`       varchar(200) NULL,
  `idMeta`            int NULL,
  `idCategoria`       int NULL,
  `idCuentaDestino`   int NULL,
  `fechaCreacion`     timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`idMovimiento`),
  KEY `idx_movimientos_cuenta_fecha` (`idCuenta`, `fechaMovimiento`),
  KEY `idx_movimientos_meta` (`idMeta`),
  KEY `idx_movimientos_categoria` (`idCategoria`),
  KEY `idx_movimientos_destino` (`idCuentaDestino`),
  CONSTRAINT `fk_movimientos_cuenta`    FOREIGN KEY (`idCuenta`)        REFERENCES `cuentas` (`idCuenta`),
  CONSTRAINT `fk_movimientos_meta`      FOREIGN KEY (`idMeta`)          REFERENCES `metas` (`idMeta`),
  CONSTRAINT `fk_movimientos_categoria` FOREIGN KEY (`idCategoria`)     REFERENCES `categorias` (`idCategoria`),
  CONSTRAINT `fk_movimientos_destino`   FOREIGN KEY (`idCuentaDestino`) REFERENCES `cuentas` (`idCuenta`),
  CONSTRAINT `chk_movimientos_monto`     CHECK (`monto` > 0),
  CONSTRAINT `chk_movimientos_meta`      CHECK (`idMeta` IS NULL OR `tipo` = 'Ingreso'),
  CONSTRAINT `chk_movimientos_categoria` CHECK (`idCategoria` IS NULL OR `tipo` = 'Retiro'),
  CONSTRAINT `chk_movimientos_destino`   CHECK (
       (`tipo` =  'Transferencia' AND `idCuentaDestino` IS NOT NULL AND `idCuentaDestino` <> `idCuenta`)
    OR (`tipo` <> 'Transferencia' AND `idCuentaDestino` IS NULL)
  )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------
-- 7. ASESORÍAS                                        -> AHO-0008
-- ---------------------------------------------------------------------
CREATE TABLE `asesorias` (
  `idAsesoria`        int NOT NULL AUTO_INCREMENT,
  `idAsesor`          int NOT NULL,
  `idUsuario`         int NOT NULL,
  `fechaAsesoria`     date NOT NULL,
  `observaciones`     varchar(500) NOT NULL,
  `fechaCreacion`     timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fechaModificacion` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`idAsesoria`),
  KEY `idx_asesorias_asesor` (`idAsesor`),
  KEY `idx_asesorias_usuario` (`idUsuario`),
  CONSTRAINT `fk_asesorias_asesor`  FOREIGN KEY (`idAsesor`)  REFERENCES `asesores` (`idAsesor`),
  CONSTRAINT `fk_asesorias_usuario` FOREIGN KEY (`idUsuario`) REFERENCES `usuarios` (`idUsuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =====================================================================
-- VISTAS DE APOYO PARA LOS REPORTES
-- (Opcionales: el requerimiento pide recorrer con for/if en Python,
--  pero estas vistas sirven para verificar que los cálculos cuadren.)
-- =====================================================================

-- AHO-0010: saldo, total ingresos y total retiros por usuario
CREATE VIEW `vw_reporte_saldo_usuario` AS
SELECT u.idUsuario,
       u.nombre,
       COALESCE(c.saldoTotal, 0)    AS saldoActual,
       COALESCE(m.totalIngresos, 0) AS totalIngresos,
       COALESCE(m.totalRetiros, 0)  AS totalRetiros
FROM usuarios u
LEFT JOIN (SELECT idUsuario, SUM(saldoActual) AS saldoTotal
           FROM cuentas GROUP BY idUsuario) c ON c.idUsuario = u.idUsuario
LEFT JOIN (SELECT cu.idUsuario,
                  SUM(CASE WHEN mo.tipo IN ('Ingreso','Interes') THEN mo.monto ELSE 0 END) AS totalIngresos,
                  SUM(CASE WHEN mo.tipo = 'Retiro'               THEN mo.monto ELSE 0 END) AS totalRetiros
           FROM movimientos mo
           JOIN cuentas cu ON cu.idCuenta = mo.idCuenta
           GROUP BY cu.idUsuario) m ON m.idUsuario = u.idUsuario;

-- AHO-0011: cumplimiento de metas con porcentaje de avance
CREATE VIEW `vw_cumplimiento_metas` AS
SELECT me.idMeta,
       u.nombre AS usuario,
       me.nombre AS meta,
       me.montoObjetivo,
       me.montoActual,
       ROUND(me.montoActual / me.montoObjetivo * 100, 2) AS porcentajeAvance,
       me.fechaLimite,
       me.estado
FROM metas me
JOIN usuarios u ON u.idUsuario = me.idUsuario;

-- AHO-0007: gasto del mes actual contra el presupuesto de cada categoría
CREATE VIEW `vw_presupuesto_categorias_mes` AS
SELECT ca.idCategoria,
       ca.idUsuario,
       ca.nombre,
       ca.presupuestoMensual,
       COALESCE(SUM(mo.monto), 0)                         AS gastadoMes,
       ca.presupuestoMensual - COALESCE(SUM(mo.monto), 0) AS disponible,
       (COALESCE(SUM(mo.monto), 0) > ca.presupuestoMensual) AS excedido
FROM categorias ca
LEFT JOIN movimientos mo
       ON mo.idCategoria = ca.idCategoria
      AND mo.tipo = 'Retiro'
      AND mo.fechaMovimiento >= DATE_FORMAT(CURDATE(), '%Y-%m-01')
      AND mo.fechaMovimiento <  DATE_FORMAT(CURDATE(), '%Y-%m-01') + INTERVAL 1 MONTH
GROUP BY ca.idCategoria, ca.idUsuario, ca.nombre, ca.presupuestoMensual;
