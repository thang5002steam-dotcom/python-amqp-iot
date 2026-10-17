"""Bài 2: đọc telemetry và phát cảnh báo theo ngưỡng."""

import json
import os
from math import isfinite

import pika


QUEUE = "sensor_data_queue"
DEFAULT_AMQP_URL = "amqp://guest:guest@localhost:5672/%2F"


def validate_reading(payload):
    if not isinstance(payload, dict):
        raise ValueError("Payload phải là JSON object")
    device_id = payload.get("device_id")
    temperature = payload.get("temperature")
    humidity = payload.get("humidity")
    if not isinstance(device_id, str) or not device_id.strip():
        raise ValueError("device_id phải là chuỗi không rỗng")
    if isinstance(temperature, bool) or not isinstance(temperature, (int, float)):
        raise ValueError("temperature phải là số")
    if isinstance(humidity, bool) or not isinstance(humidity, (int, float)):
        raise ValueError("humidity phải là số")
    if not isfinite(temperature) or not isfinite(humidity):
        raise ValueError("temperature và humidity phải là số hữu hạn")
    if not -100 <= temperature <= 150:
        raise ValueError("temperature nằm ngoài phạm vi hợp lý")
    if not 0 <= humidity <= 100:
        raise ValueError("humidity phải nằm trong khoảng 0–100")
    return device_id.strip(), temperature, humidity


def main():
    parameters = pika.URLParameters(os.getenv("AMQP_URL", DEFAULT_AMQP_URL))
    connection = pika.BlockingConnection(parameters)
    try:
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE, durable=True)
        channel.basic_qos(prefetch_count=1)

        def on_message(ch, method, _properties, body):
            try:
                payload = json.loads(body.decode("utf-8"))
                device_id, temperature, humidity = validate_reading(payload)
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
                print(f"Bo qua telemetry khong hop le: {exc}", flush=True)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return
            print(f"Device: {device_id}")
            print(f"Temperature: {temperature:.1f}")
            print(f"Humidity: {humidity:.1f}")
            if temperature > 35:
                print("CANH BAO: Nhiet do cao")
            if humidity < 40:
                print("CANH BAO: Do am thap")
            print(flush=True)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_consume(queue=QUEUE, on_message_callback=on_message, auto_ack=False)
        print(f"Dang lang nghe {QUEUE}. Nhan Ctrl+C de dung.", flush=True)
        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            channel.stop_consuming()
            print("Da dung monitoring consumer.")
    finally:
        if connection.is_open:
            connection.close()


if __name__ == "__main__":
    main()
