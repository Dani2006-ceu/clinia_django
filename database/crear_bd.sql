-- =====================================================================
-- Sonrisa Perfecta - creación de la base de datos en MariaDB
-- Ejecutar como root (phpMyAdmin > SQL, o desde consola):
--   C:\xampp\mysql\bin\mysql.exe -u root -p < database\crear_bd.sql
-- Las TABLAS las crea Django con: python manage.py migrate
-- =====================================================================

CREATE DATABASE IF NOT EXISTS sonrisa_perfecta
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Usuario propio de la aplicación (no usar root en la aplicación).
-- Cambie la contraseña y use la misma en DB_PASSWORD del archivo .env
CREATE USER IF NOT EXISTS 'sonrisa_user'@'localhost' IDENTIFIED BY 'Sonrisa2026*';
CREATE USER IF NOT EXISTS 'sonrisa_user'@'127.0.0.1' IDENTIFIED BY 'Sonrisa2026*';

GRANT ALL PRIVILEGES ON sonrisa_perfecta.* TO 'sonrisa_user'@'localhost';
GRANT ALL PRIVILEGES ON sonrisa_perfecta.* TO 'sonrisa_user'@'127.0.0.1';
FLUSH PRIVILEGES;
