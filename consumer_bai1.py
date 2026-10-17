"""Bài 1: nhận lời chào liên tục và in thời điểm nhận."""

from datetime import datetime

from amqp_common import BASIC_QUEUE, close_connection, create_connection


def main():
    connection = create_connection()
    try:
        channel = connection.channel()
        channel.queue_declare(queue=BASIC_QUEUE, durable=True)
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

        channel.basic_consume(queue=BASIC_QUEUE, on_message_callback=on_message, auto_ack=False)
        print(f"Dang lang nghe {BASIC_QUEUE}. Nhan Ctrl+C de dung.", flush=True)
        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            channel.stop_consuming()
            print("Da dung consumer.")
    finally:
        close_connection(connection)


if __name__ == "__main__":
    main()
