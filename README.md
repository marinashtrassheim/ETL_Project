# Итоговое задание 3 модуля
ETL_Project/
├── .env
├── airflow/
│   ├── Dockerfile
│   ├── airflow.cfg
│   ├── requirements.txt
│   └── dags/
│       ├── DAG_event_logs_etl.py
│       ├── DAG_price_history_etl.py
│       └── DAG_user_activity_etl.py
├── data_creator/
│   ├── Dockerfile
│   ├── mongo_generate_data.py
│   └── requirements.txt
├── mongo/
│   └── Dockerfile
├── postgres/
│   ├── Dockerfile
│   └── db_setup_scripts/
│       ├── airflow_db_setup.sql
│       ├── app_db_setup.sql
│       └── initialize_db.sh
└── docker-compose.yml
