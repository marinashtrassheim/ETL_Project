-- Создание базы данных и пользователя для приложения
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${APP_DB_USER}') THEN
        CREATE ROLE ${APP_DB_USER} WITH LOGIN PASSWORD '${APP_DB_PASSWORD}';
    END IF;
END $$;

CREATE DATABASE ${APP_DB_NAME};

-- Назначение прав пользователю
GRANT ALL PRIVILEGES ON DATABASE ${APP_DB_NAME} TO ${APP_DB_USER};

-- Подключение к базе данных
\c ${APP_DB_NAME}

-- Создание схемы и настройка прав
CREATE SCHEMA IF NOT EXISTS ${APP_DB_SCHEMA} AUTHORIZATION ${APP_DB_USER};
ALTER ROLE ${APP_DB_USER} SET search_path TO ${APP_DB_SCHEMA};

-- Настройка прав по умолчанию
ALTER DEFAULT PRIVILEGES IN SCHEMA ${APP_DB_SCHEMA} GRANT ALL ON TABLES TO ${APP_DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA ${APP_DB_SCHEMA} GRANT USAGE ON SEQUENCES TO ${APP_DB_USER};
