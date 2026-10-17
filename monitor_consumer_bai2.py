"""Bài 2: nhận telemetry, hiển thị dữ liệu và kiểm tra ngưỡng."""

import json

from amqp_common import SENSOR_QUEUE, close_connection, create_connection
from message_utils import sensor_warnings, validate_sensor_reading


def main():
    connection = create_connection()
    try:
        channel = connection.channel()
        channel.queue_declare(queue=SENSOR_QUEUE, durable=True)
        channel.basic_qos(prefetch_count=1)

        def on_message(ch, method, _properties, body):
            try:
                payload = json.loads(body.decode("utf-8"))
                device_id, temperature, humidity = validate_sensor_reading(payload)
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
                print(f"Bo qua telemetry khong hop le: {exc}", flush=True)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return
            print(f"Device: {device_id}")
            print(f"Temperature: {temperature:.1f}")
            print(f"Humidity: {humidity:.1f}")
            for warning in sensor_warnings(temperature, humidity):
                print(warning)
            print(flush=True)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_consume(queue=SENSOR_QUEUE, on_message_callback=on_message, auto_ack=False)
        print(f"Dang lang nghe {SENSOR_QUEUE}. Nhan Ctrl+C de dung.", flush=True)
        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            channel.stop_consuming()
            print("Da dung monitoring consumer.")
    finally:
        close_connection(connection)


if __name__ == "__main__":
    main()
