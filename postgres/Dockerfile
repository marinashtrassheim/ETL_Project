FROM postgres:17-bookworm

# Установка необходимых утилит
RUN apt-get update && apt-get install -y \
    gettext-base

# Копирование SQL-скриптов и скрипта инициализации
COPY db_setup_scripts/ /docker-entrypoint-initdb.d/

# Назначение прав на скрипт инициализации
RUN chmod +x /docker-entrypoint-initdb.d/initialize_db.sh
