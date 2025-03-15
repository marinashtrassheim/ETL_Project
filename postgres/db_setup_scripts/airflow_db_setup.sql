-- Создание пользователя и базы данных для Airflow
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${AIRFLOW_USER}') THEN
        CREATE ROLE ${AIRFLOW_USER} WITH LOGIN PASSWORD '${AIRFLOW_PASSWORD}' CREATEDB;
    END IF;
END $$;

CREATE DATABASE ${AIRFLOW_DB}
    WITH
    OWNER = ${AIRFLOW_USER}
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;
