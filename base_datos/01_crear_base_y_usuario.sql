-- =====================================================================
-- HoraSalud - Paso 1: crear la base y el usuario de la aplicacion
-- (misma PARTE 1 de SRC03-C05-Src_ScriptsBaseDatos.sql)
--
-- ANTES DE EJECUTAR: cambia  tu_clave  por una clave inventada por ti.
-- Esa clave va despues en el archivo .env (DB_PASSWORD).
-- La clave NO se escribe en este archivo del repositorio: solo en tu copia.
--
-- phpMyAdmin -> pestana SQL -> pegar -> Continuar.
-- =====================================================================
CREATE DATABASE IF NOT EXISTS horasalud_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'horasalud_app'@'localhost' IDENTIFIED BY 'tu_clave';
GRANT ALL PRIVILEGES ON horasalud_db.* TO 'horasalud_app'@'localhost';
GRANT ALL PRIVILEGES ON test_horasalud_db.* TO 'horasalud_app'@'localhost';

-- FONASA simulado: sistema EXTERNO en su propia base (padrón de 25 personas ficticias)
CREATE DATABASE IF NOT EXISTS fonasa_simulado CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON fonasa_simulado.* TO 'horasalud_app'@'localhost';
GRANT ALL PRIVILEGES ON test_fonasa_simulado.* TO 'horasalud_app'@'localhost';
FLUSH PRIVILEGES;
