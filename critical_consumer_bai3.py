"""Bài 3: chỉ nhận cảnh báo có routing key critical."""

from amqp_common import ALERT_EXCHANGE, CRITICAL_QUEUE, close_connection, create_connection


def main():
    connection = create_connection()
    try:
        channel = connection.channel()
        channel.exchange_declare(exchange=ALERT_EXCHANGE, exchange_type="direct", durable=True)
        channel.queue_declare(queue=CRITICAL_QUEUE, durable=True)
        channel.queue_bind(queue=CRITICAL_QUEUE, exchange=ALERT_EXCHANGE, routing_key="critical")
        channel.basic_qos(prefetch_count=1)

        def on_message(ch, method, _properties, body):
            try:
                message = body.decode("utf-8")
            except UnicodeDecodeError as exc:
                print(f"Bo qua message khong phai UTF-8: {exc}", flush=True)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return
            print(f"[{CRITICAL_QUEUE}] Da nhan: {message}", flush=True)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_consume(queue=CRITICAL_QUEUE, on_message_callback=on_message, auto_ack=False)
        print(f"Dang lang nghe {CRITICAL_QUEUE}. Nhan Ctrl+C de dung.", flush=True)
        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            channel.stop_consuming()
            print("Da dung critical consumer.")
    finally:
        close_connection(connection)


if __name__ == "__main__":
    main()
