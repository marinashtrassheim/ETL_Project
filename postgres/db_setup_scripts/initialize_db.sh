#!/bin/bash

# Создание временной директории для SQL-скриптов
TEMP_SQL_DIR="/tmp/sql_setup"
mkdir -p ${TEMP_SQL_DIR}

# Подстановка переменных окружения в SQL-шаблоны
envsubst < /docker-entrypoint-initdb.d/airflow_db_setup.sql > ${TEMP_SQL_DIR}/airflow_db.sql
envsubst < /docker-entrypoint-initdb.d/app_db_setup.sql > ${TEMP_SQL_DIR}/app_db.sql

# Выполнение SQL-скриптов
psql -v ON_ERROR_STOP=1 -U "postgres" -f ${TEMP_SQL_DIR}/airflow_db.sql
psql -v ON_ERROR_STOP=1 -U "postgres" -f ${TEMP_SQL_DIR}/app_db.sql

# Очистка временной директории
rm -rf ${TEMP_SQL_DIR}
