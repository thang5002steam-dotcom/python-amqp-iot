"""Bài 2: gửi telemetry JSON của một hoặc nhiều cảm biến mỗi 3 giây."""

import argparse
import json
import time

import pika

from amqp_common import SENSOR_QUEUE, close_connection, create_connection
from message_utils import sensor_reading


def main():
    parser = argparse.ArgumentParser(description="Mô phỏng cảm biến IoT")
    parser.add_argument(
        "--device-id", action="append", help="Có thể lặp lại để mô phỏng 2–3 cảm biến"
    )
    parser.add_argument(
        "--count", type=int, default=0, help="Số lượt gửi; 0 là gửi liên tục (mặc định)"
    )
    args = parser.parse_args()
    if args.count < 0:
        parser.error("--count không được âm")
    device_ids = args.device_id or ["sensor01"]
    if any(not item.strip() for item in device_ids):
        parser.error("--device-id không được để trống")

    connection = create_connection()
    try:
        channel = connection.channel()
        channel.queue_declare(queue=SENSOR_QUEUE, durable=True)
        channel.confirm_delivery()
        print(f"Dang gui du lieu moi 3 giay cho {', '.join(device_ids)}. Nhan Ctrl+C de dung.")
        round_number = 0
        try:
            while args.count == 0 or round_number < args.count:
                for device_id in device_ids:
                    payload = sensor_reading(device_id)
                    channel.basic_publish(
                        exchange="",
                        routing_key=SENSOR_QUEUE,
                        body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                        properties=pika.BasicProperties(
                            content_type="application/json", delivery_mode=2
                        ),
                        mandatory=True,
                    )
                    print(f"Da gui: {json.dumps(payload, ensure_ascii=False)}", flush=True)
                round_number += 1
                if args.count == 0 or round_number < args.count:
                    time.sleep(3)
        except KeyboardInterrupt:
            print("Da dung sensor producer.")
    finally:
        close_connection(connection)


if __name__ == "__main__":
    main()
