import os
import random
import uuid
from datetime import datetime, timedelta
from faker import Faker
from pymongo import MongoClient
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Подключение к MongoDB
mongo_connection_string = os.getenv("MONGO_URI", "mongodb://admin:admin@mongo:27017")
mongo_client = MongoClient(mongo_connection_string)
database = mongo_client[os.getenv("MONGO_DB")]

# Инициализация Faker для генерации случайных данных
fake_generator = Faker()

# Функция для получения количества записей из переменных окружения
def fetch_record_count(env_var, default_value):
    return int(os.getenv(env_var, default_value))

# Генерация уникальных идентификаторов для пользователей и товаров
user_ids = [str(uuid.uuid4()) for _ in range(fetch_record_count("USER_COUNT", 1000))]
product_ids = [str(uuid.uuid4()) for _ in range(fetch_record_count("PRODUCT_COUNT", 500))]

# Функции для создания данных
def create_user_sessions(record_count):
    """Создание данных о сессиях пользователей."""
    return [{
        "session_identifier": str(uuid.uuid4()),
        "user_identifier": random.choice(user_ids),
        "session_start": (start_time := fake_generator.date_time_this_year()).isoformat(),
        "session_end": (start_time + timedelta(minutes=random.randint(5, 120))).isoformat(),
        "visited_pages": [fake_generator.uri_path() for _ in range(random.randint(1, 10))],
        "user_device": fake_generator.user_agent(),
        "user_actions": [fake_generator.word() for _ in range(random.randint(1, 5))]
    } for _ in range(record_count)]

def create_price_changes(record_count):
    """Создание истории изменения цен на товары."""
    return [{
        "product_identifier": random.choice(product_ids),
        "price_updates": [{
            "update_date": (datetime.now() - timedelta(days=i)).isoformat(),
            "updated_price": round(random.uniform(10, 1000), 2)
        } for i in range(random.randint(1, 10))],
        "latest_price": round(random.uniform(10, 1000), 2),
        "price_currency": "USD"
    } for _ in range(record_count)]

def create_event_records(record_count):
    """Создание логов событий."""
    events = ["login", "logout", "purchase", "error", "click"]
    return [{
        "event_identifier": str(uuid.uuid4()),
        "event_time": fake_generator.date_time_this_year().isoformat(),
        "event_category": random.choice(events),
        "event_details": fake_generator.sentence()
    } for _ in range(record_count)]

def create_support_requests(record_count):
    """Создание запросов в службу поддержки."""
    ticket_statuses = ["open", "closed", "pending"]
    issues_list = ["login issue", "payment failure", "bug report", "feature request"]
    return [{
        "ticket_identifier": str(uuid.uuid4()),
        "user_identifier": random.choice(user_ids),
        "ticket_status": random.choice(ticket_statuses),
        "issue_category": random.choice(issues_list),
        "conversation": [fake_generator.sentence() for _ in range(random.randint(1, 5))],
        "created_on": fake_generator.date_time_this_year().isoformat(),
        "last_updated": fake_generator.date_time_this_year().isoformat()
    } for _ in range(record_count)]

def create_user_suggestions(record_count):
    """Создание рекомендаций для пользователей."""
    return [{
        "user_identifier": random.choice(user_ids),
        "suggested_items": [random.choice(product_ids) for _ in range(random.randint(1, 5))],
        "last_suggestion_update": fake_generator.date_time_this_year().isoformat()
    } for _ in range(record_count)]

def create_review_moderation(record_count):
    """Создание очереди модерации отзывов."""
    moderation_statuses = ["pending", "approved", "rejected"]
    return [{
        "review_identifier": str(uuid.uuid4()),
        "user_identifier": random.choice(user_ids),
        "product_identifier": random.choice(product_ids),
        "review_content": fake_generator.text(),
        "product_rating": random.randint(1, 5),
        "moderation_state": random.choice(moderation_statuses),
        "review_flags": [fake_generator.word() for _ in range(random.randint(0, 3))],
        "submission_date": fake_generator.date_time_this_year().isoformat()
    } for _ in range(record_count)]

def create_search_history(record_count):
    """Создание истории поисковых запросов."""
    return [{
        "search_identifier": str(uuid.uuid4()),
        "user_identifier": random.choice(user_ids),
        "search_query": fake_generator.sentence(),
        "query_time": fake_generator.date_time_this_year().isoformat(),
        "applied_filters": [fake_generator.word() for _ in range(random.randint(0, 3))],
        "results_found": random.randint(0, 50)
    } for _ in range(record_count)]

print("Запуск генерации данных...")

# Генерация и вставка данных в MongoDB
sessions_count = fetch_record_count("USER_SESSIONS_COUNT", 1000)
database.user_sessions.insert_many(create_user_sessions(sessions_count))

price_history_count = fetch_record_count("PRODUCT_PRICE_HISTORY_COUNT", 1000)
database.product_price_history.insert_many(create_price_changes(price_history_count))

event_logs_count = fetch_record_count("EVENT_LOGS_COUNT", 2000)
database.event_logs.insert_many(create_event_records(event_logs_count))

support_tickets_count = fetch_record_count("SUPPORT_TICKETS_COUNT", 500)
database.support_tickets.insert_many(create_support_requests(support_tickets_count))

user_recommendations_count = fetch_record_count("USER_RECOMMENDATIONS_COUNT", 1000)
database.user_recommendations.insert_many(create_user_suggestions(user_recommendations_count))

moderation_queue_count = fetch_record_count("MODERATION_QUEUE_COUNT", 500)
database.moderation_queue.insert_many(create_review_moderation(moderation_queue_count))

search_queries_count = fetch_record_count("SEARCH_QUERIES_COUNT", 1000)
database.search_queries.insert_many(create_search_history(search_queries_count))


print("Все данные успешно загружены в MongoDB.")