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
DAG_NAME = "price_history_etl"
COLLECTION_NAME = "product_price_history"

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
    tags=["etl", "price_history"],
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

    # Разворачиваем историю цен в отдельные строки
    df_exploded = df.explode("price_changes").reset_index(drop=True)

    # Нормализуем словари в price_changes
    price_history_df = df_exploded["price_changes"].apply(pd.Series)

    # Объединяем с исходными данными
    df_transformed = pd.concat([df_exploded.drop(columns=["price_changes"]), price_history_df], axis=1)

    # Фильтрация данных: удаление записей с нулевой ценой
    df_transformed = df_transformed[df_transformed["price"] > 0]

    # Добавление вычисляемого поля: разница между текущей и предыдущей ценой
    df_transformed["price_diff"] = df_transformed.groupby("product_id")["price"].diff().fillna(0)

    # Удаление дубликатов
    df_transformed.drop_duplicates(subset=["product_id", "date"], inplace=True)

    # Логирование статистики
    logger.info(f"Трансформировано {len(df_transformed)} записей.")
    logger.info(f"Средняя цена: {df_transformed['price'].mean()}")
    logger.info(f"Количество изменений цены: {len(df_transformed)}")

    # Передача данных в XCom
    ti.xcom_push(key='transformed_data', value=df_transformed.to_dict(orient='records'))

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
    df['date'] = pd.to_datetime(df['date'])

    # Устанавливаем индекс
    df.set_index(["product_id", "date"], inplace=True)

    # Загрузка данных в PostgreSQL
    df.to_sql(
        COLLECTION_NAME,
        schema="source",
        con=engine,
        if_exists="append",
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