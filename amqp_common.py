"""Cấu hình kết nối và tên AMQP dùng chung cho ba bài thực hành."""

import os

import pika


BASIC_QUEUE = "iot_lab_queue"
SENSOR_QUEUE = "sensor_data_queue"
ALERT_EXCHANGE = "iot_alert_exchange"
WARNING_QUEUE = "warning_queue"
CRITICAL_QUEUE = "critical_queue"


def create_connection():
    """Kết nối broker qua AMQP_URL hoặc các biến RABBITMQ_*."""
    url = os.getenv("AMQP_URL")
    if url:
        parameters = pika.URLParameters(url)
    else:
        credentials = pika.PlainCredentials(
            os.getenv("RABBITMQ_USER", "guest"),
            os.getenv("RABBITMQ_PASSWORD", "guest"),
        )
        parameters = pika.ConnectionParameters(
            host=os.getenv("RABBITMQ_HOST", "localhost"),
            port=int(os.getenv("RABBITMQ_PORT", "5672")),
            virtual_host=os.getenv("RABBITMQ_VHOST", "/"),
            credentials=credentials,
            heartbeat=60,
            blocked_connection_timeout=30,
            connection_attempts=3,
            retry_delay=2,
        )
    return pika.BlockingConnection(parameters)


def close_connection(connection):
    if connection.is_open:
        connection.close()
