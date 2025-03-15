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
DAG_NAME = "event_processing_etl"
COLLECTION_NAME = "event_logs"

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
    tags=["etl", "event_processing"],
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

    # Фильтрация данных: удаление событий с пустыми значениями
    df.dropna(subset=["event_id", "timestamp"], inplace=True)

    # Категоризация событий
    df["event_category"] = df["event_type"].apply(
        lambda x: "user_action" if x in ["login", "logout", "click"] else "system_event"
    )

    # Удаление дубликатов
    df.drop_duplicates(subset=["event_id"], inplace=True)

    # Логирование статистики
    logger.info(f"Трансформировано {len(df)} записей.")
    logger.info(f"Количество событий по категориям:\n{df['event_category'].value_counts()}")

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

    # Преобразуем поля
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Устанавливаем индекс
    df.set_index("event_id", inplace=True)

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
    # Удаляем дубликаты и заполняем нули
    df.drop_duplicates(subset=["event_id"], inplace=True)
    df.fillna("", inplace=True)


    logging.info(f"Трансформировано {len(df)} записей")
    ti.xcom_push(key='transformed_data', value=df.to_dict(orient='records'))

def load(**kwargs):
    """Загружает данные в PostgreSQL"""
    ti = kwargs['ti']
    transformed_data = ti.xcom_pull(task_ids='transform', key='transformed_data')

    if not transformed_data:
        logging.warning("Нет данных для загрузки")
        return

    pg_hook = PostgresHook(postgres_conn_id="etl_postgres")
    engine = pg_hook.get_sqlalchemy_engine()

    df = pd.DataFrame(transformed_data)

    # Преобразуем start_time в datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    #Устанавливаем индекс
    df.set_index("event_id", inplace=True)

    # Загружаем данные в PostgreSQL
    df.to_sql(collection_name, schema="source", con=engine, if_exists="replace", index=True)

    logging.info(f"Загружено {len(df)} записей в PostgreSQL")

# Заглушки
task_start = DummyOperator(task_id='start', dag=dag)
task_finish = DummyOperator(task_id='finish', dag=dag)

task_extract = PythonOperator(task_id='extract', python_callable=extract, provide_context=True, dag=dag)
task_transform = PythonOperator(task_id='transform', python_callable=transform, provide_context=True, dag=dag)
task_load = PythonOperator(task_id='load', python_callable=load, provide_context=True, dag=dag)

# Определяем порядок выполнения
task_start >> task_extract >> task_transform >> task_load >> task_finish
