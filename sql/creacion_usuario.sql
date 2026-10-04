-- Nota: NO utilizar root desde la aplicación Python.
-- Cambia suPassword por el password que desees (el profe recomienda tu nro de identificación).
-- Ejecutar DESPUÉS de creacion_schema.sql, con root o un usuario administrador.

DROP USER IF EXISTS 'ahorro_app'@'localhost';
CREATE USER 'ahorro_app'@'localhost' IDENTIFIED WITH caching_sha2_password BY '12345678';

-- Solo los permisos que necesita el programa (CRUD), nada de DROP ni CREATE
GRANT SELECT, INSERT, UPDATE, DELETE ON `ahorroapp`.* TO 'ahorro_app'@'localhost';
FLUSH PRIVILEGES;

-- Evidencia para el entregable 2.d (imágenes del perfil y privilegios):
-- toma captura del resultado de estas dos consultas, y además de
-- Workbench > Administration > Users and Privileges > ahorro_app
-- (pestañas "Login" y "Schema Privileges").
SELECT user, host, plugin FROM mysql.user WHERE user = 'ahorro_app';
SHOW GRANTS FOR 'ahorro_app'@'localhost';
