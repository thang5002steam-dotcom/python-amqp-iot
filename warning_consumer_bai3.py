"""Bài 3: chỉ nhận cảnh báo có routing key warning."""

import os

import pika


EXCHANGE = "iot_alert_exchange"
QUEUE = "warning_queue"
DEFAULT_AMQP_URL = "amqp://guest:guest@localhost:5672/%2F"


def main():
    parameters = pika.URLParameters(os.getenv("AMQP_URL", DEFAULT_AMQP_URL))
    connection = pika.BlockingConnection(parameters)
    try:
        channel = connection.channel()
        channel.exchange_declare(exchange=EXCHANGE, exchange_type="direct", durable=True)
        channel.queue_declare(queue=QUEUE, durable=True)
        channel.queue_bind(queue=QUEUE, exchange=EXCHANGE, routing_key="warning")
        channel.basic_qos(prefetch_count=1)

        def on_message(ch, method, _properties, body):
            try:
                message = body.decode("utf-8")
            except UnicodeDecodeError as exc:
                print(f"Bo qua message khong phai UTF-8: {exc}", flush=True)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return
            print(f"[{QUEUE}] Da nhan: {message}", flush=True)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_consume(queue=QUEUE, on_message_callback=on_message, auto_ack=False)
        print(f"Dang lang nghe {QUEUE}. Nhan Ctrl+C de dung.", flush=True)
        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            channel.stop_consuming()
            print("Da dung warning consumer.")
    finally:
        if connection.is_open:
            connection.close()


if __name__ == "__main__":
    main()
