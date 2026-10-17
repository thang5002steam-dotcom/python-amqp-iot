"""Bài 3: gửi cảnh báo qua direct exchange theo routing key."""

import argparse
import os

import pika


EXCHANGE = "iot_alert_exchange"
DEFAULT_AMQP_URL = "amqp://guest:guest@localhost:5672/%2F"
ALERT_LEVELS = ("info", "warning", "critical")
SAMPLE_ALERTS = (
    ("info", "He thong IoT dang hoat dong binh thuong"),
    ("warning", "Nhiet do phong may vuot nguong warning"),
    ("critical", "Cam bien kho lanh mat ket noi critical"),
)


def main():
    parser = argparse.ArgumentParser(description="Gửi cảnh báo qua direct exchange")
    parser.add_argument("--level", choices=ALERT_LEVELS, help="Mức cảnh báo cần gửi")
    parser.add_argument("--message", help="Nội dung cảnh báo tự chọn")
    args = parser.parse_args()
    if args.message is not None and not args.level:
        parser.error("--message cần đi kèm --level")
    if args.message is not None and not args.message.strip():
        parser.error("--message không được để trống")
    alerts = (
        [(args.level, args.message or f"Canh bao muc {args.level}")]
        if args.level
        else SAMPLE_ALERTS
    )

    parameters = pika.URLParameters(os.getenv("AMQP_URL", DEFAULT_AMQP_URL))
    connection = pika.BlockingConnection(parameters)
    try:
        channel = connection.channel()
        channel.exchange_declare(exchange=EXCHANGE, exchange_type="direct", durable=True)
        channel.confirm_delivery()
        for level, message in alerts:
            channel.basic_publish(
                exchange=EXCHANGE,
                routing_key=level,
                body=message.encode("utf-8"),
                properties=pika.BasicProperties(content_type="text/plain", delivery_mode=2),
            )
            print(f"Da gui [{level}]: {message}")
    finally:
        if connection.is_open:
            connection.close()


if __name__ == "__main__":
    main()
