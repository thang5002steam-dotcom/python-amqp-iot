"""Bài 1: gửi lời chào của sinh viên vào RabbitMQ."""

import argparse
import os

import pika


QUEUE = "iot_lab_queue"
DEFAULT_AMQP_URL = "amqp://guest:guest@localhost:5672/%2F"


def main():
    parser = argparse.ArgumentParser(description="Gửi lời chào qua RabbitMQ")
    parser.add_argument("--student-id", required=True, help="Mã sinh viên")
    parser.add_argument("--student-name", required=True, help="Họ tên sinh viên")
    parser.add_argument("--greeting", default="Xin chao tu ung dung Python AMQP")
    parser.add_argument("--count", type=int, default=1, help="Số lần gửi")
    args = parser.parse_args()

    student_id = args.student_id.strip()
    student_name = args.student_name.strip()
    greeting = args.greeting.strip()
    if not all((student_id, student_name, greeting)):
        parser.error("Mã sinh viên, họ tên và lời chào không được để trống")
    if args.count < 1:
        parser.error("--count phải từ 1 trở lên")

    message = f"{greeting} - {student_id} - {student_name}"
    parameters = pika.URLParameters(os.getenv("AMQP_URL", DEFAULT_AMQP_URL))
    connection = pika.BlockingConnection(parameters)
    try:
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE, durable=True)
        channel.confirm_delivery()
        for index in range(args.count):
            channel.basic_publish(
                exchange="",
                routing_key=QUEUE,
                body=message.encode("utf-8"),
                properties=pika.BasicProperties(content_type="text/plain", delivery_mode=2),
                mandatory=True,
            )
            print(f"Da gui {index + 1}/{args.count}: {message}")
    finally:
        if connection.is_open:
            connection.close()


if __name__ == "__main__":
    main()
