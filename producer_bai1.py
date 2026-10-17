"""Bài 1: gửi lời chào của sinh viên vào iot_lab_queue."""

import argparse

import pika

from amqp_common import BASIC_QUEUE, close_connection, create_connection
from message_utils import student_message


def main():
    parser = argparse.ArgumentParser(description="Gửi lời chào qua RabbitMQ")
    parser.add_argument("--student-id", required=True, help="Mã sinh viên")
    parser.add_argument("--student-name", required=True, help="Họ tên sinh viên")
    parser.add_argument(
        "--greeting", default="Xin chao tu ung dung Python AMQP", help="Nội dung chào mừng"
    )
    parser.add_argument("--count", type=int, default=1, help="Số message cần gửi (mặc định: 1)")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count phải từ 1 trở lên")
    try:
        message = student_message(args.student_id, args.student_name, args.greeting)
    except ValueError as exc:
        parser.error(str(exc))

    connection = create_connection()
    try:
        channel = connection.channel()
        channel.queue_declare(queue=BASIC_QUEUE, durable=True)
        channel.confirm_delivery()
        for index in range(args.count):
            channel.basic_publish(
                exchange="",
                routing_key=BASIC_QUEUE,
                body=message.encode("utf-8"),
                properties=pika.BasicProperties(content_type="text/plain", delivery_mode=2),
                mandatory=True,
            )
            print(f"Da gui {index + 1}/{args.count}: {message}")
    finally:
        close_connection(connection)


if __name__ == "__main__":
    main()
