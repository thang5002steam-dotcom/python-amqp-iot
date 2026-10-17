"""Bài 1: nhận lời chào và in thời điểm nhận."""

import os
from datetime import datetime

import pika


QUEUE = "iot_lab_queue"
DEFAULT_AMQP_URL = "amqp://guest:guest@localhost:5672/%2F"


def main():
    parameters = pika.URLParameters(os.getenv("AMQP_URL", DEFAULT_AMQP_URL))
    connection = pika.BlockingConnection(parameters)
    try:
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE, durable=True)
        channel.basic_qos(prefetch_count=1)

        def on_message(ch, method, _properties, body):
            try:
                message = body.decode("utf-8")
            except UnicodeDecodeError as exc:
                print(f"Bo qua message khong phai UTF-8: {exc}", flush=True)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return
            print(f"Da nhan message: {message}", flush=True)
            print(f"Thoi gian nhan: {datetime.now().astimezone():%H:%M:%S}", flush=True)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_consume(queue=QUEUE, on_message_callback=on_message, auto_ack=False)
        print(f"Dang lang nghe {QUEUE}. Nhan Ctrl+C de dung.", flush=True)
        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            channel.stop_consuming()
            print("Da dung consumer.")
    finally:
        if connection.is_open:
            connection.close()


if __name__ == "__main__":
    main()
