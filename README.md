# Итоговое задание 3 модуля
ETL_Project/( \n )
├── .env
├── airflow/
│   ( \t )├── Dockerfile
│   ( \t )├── airflow.cfg
│   ( \t )├── requirements.txt
│   ( \t )└── dags/
│       ( \t )( \t )├── DAG_event_logs_etl.py
│       ( \t )( \t )├── DAG_price_history_etl.py
│       ( \t )( \t )└── DAG_user_activity_etl.py
├── ( \t )data_creator/
│   ( \t )( \t )├── Dockerfile
│   ( \t )( \t )├── mongo_generate_data.py
│   ( \t )( \t )└── requirements.txt
├── ( \t )mongo/
│   ( \t )( \t )└── Dockerfile
├── ( \t )postgres/
│   ( \t )( \t )├── Dockerfile
│   ( \t )( \t )── db_setup_scripts/
│       ( \t )( \t )( \t )├── airflow_db_setup.sql
│       ( \t )( \t )( \t )├── app_db_setup.sql
│       └( \t )( \t )( \t )── initialize_db.sh
└── docker-compose.yml
