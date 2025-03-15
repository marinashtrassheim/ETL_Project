import logging
import os
from datetime import datetime
import pandas as pd
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.providers.mongo.hooks.mongo import MongoHook
from airflow.providers.postgres.hooks.postgres import PostgresHook

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Название DAG и коллекции
DAG_NAME = "user_sessions_etl"
COLLECTION_NAME = "user_sessions"

# Аргументы DAG
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 3, 11),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Создание DAG
dag = DAG(
    DAG_NAME,
    default_args=default_args,
    schedule_interval="@daily",
    catchup=False,
    tags=["etl", "user_sessions"],
)

def extract_data(**kwargs):
    """Извлечение данных из MongoDB."""
    mongo_hook = MongoHook(mongo_conn_id='etl_mongo')
    client = mongo_hook.get_conn()
    db_name = os.getenv("MONGO_DB", "source_db")
    collection = client[db_name][COLLECTION_NAME]

    # Извлечение данных
    extracted_data = list(collection.find({}, {"_id": 0}))
    logger.info(f"Извлечено {len(extracted_data)} записей из MongoDB.")

    # Передача данных в XCom
    kwargs['ti'].xcom_push(key='extracted_data', value=extracted_data)

def transform_data(**kwargs):
    """Трансформация данных."""
    ti = kwargs['ti']
    extracted_data = ti.xcom_pull(task_ids='extract_data', key='extracted_data')

    if not extracted_data:
        logger.warning("Нет данных для трансформации.")
        return

    # Преобразование в DataFrame
    df = pd.DataFrame(extracted_data)

    # Преобразование времени в datetime
    df['session_start'] = pd.to_datetime(df['session_start'])
    df['session_end'] = pd.to_datetime(df['session_end'])

    # Фильтрация данных: удаление сессий, где start_time > end_time
    df = df[df['session_start'] <= df['session_end']]

    # Обработка списков
    df['visited_pages'] = df['visited_pages'].apply(lambda x: ', '.join(x) if isinstance(x, list) else 'N/A')
    df['user_actions'] = df['user_actions'].apply(lambda x: ', '.join(x) if isinstance(x, list) else 'N/A')

    # Удаление дубликатов по session_identifier
    df.drop_duplicates(subset=["session_identifier"], inplace=True)

    # Логирование статистики
    logger.info(f"Трансформировано {len(df)} записей.")
    logger.info(f"Средняя длительность сессии: {(df['session_end'] - df['session_start']).mean()}")

    # Передача данных в XCom
    ti.xcom_push(key='transformed_data', value=df.to_dict(orient='records'))

def load_data(**kwargs):
    """Загрузка данных в PostgreSQL."""
    ti = kwargs['ti']
    transformed_data = ti.xcom_pull(task_ids='transform_data', key='transformed_data')

    if not transformed_data:
        logger.warning("Нет данных для загрузки.")
        return

    pg_hook = PostgresHook(postgres_conn_id="etl_postgres")
    engine = pg_hook.get_sqlalchemy_engine()

    df = pd.DataFrame(transformed_data)

    # Установка индекса
    df.set_index("session_identifier", inplace=True)

    # Загрузка данных в PostgreSQL
    df.to_sql(
        COLLECTION_NAME,
        schema="source",
        con=engine,
        if_exists="replace",
        index=True,
        method="multi",
    )
    logger.info(f"Загружено {len(df)} записей в PostgreSQL.")

# Задачи DAG
task_start = DummyOperator(task_id='start', dag=dag)
task_extract = PythonOperator(task_id='extract_data', python_callable=extract_data, provide_context=True, dag=dag)
task_transform = PythonOperator(task_id='transform_data', python_callable=transform_data, provide_context=True, dag=dag)
task_load = PythonOperator(task_id='load_data', python_callable=load_data, provide_context=True, dag=dag)
task_finish = DummyOperator(task_id='finish', dag=dag)

# Определение порядка выполнения задач
task_start >> task_extract >> task_transform >> task_load >> task_finish