"""Bài 2: mô phỏng một hoặc nhiều cảm biến IoT, gửi JSON mỗi 3 giây."""

import argparse
import json
import os
import random
import time
from datetime import datetime, timezone

import pika


QUEUE = "sensor_data_queue"
DEFAULT_AMQP_URL = "amqp://guest:guest@localhost:5672/%2F"


def main():
    parser = argparse.ArgumentParser(description="Mô phỏng cảm biến IoT")
    parser.add_argument("--device-id", action="append", help="Lặp lại để dùng nhiều cảm biến")
    parser.add_argument("--count", type=int, default=0, help="Số lượt; 0 là gửi liên tục")
    args = parser.parse_args()
    if args.count < 0:
        parser.error("--count không được âm")
    device_ids = args.device_id or ["sensor01"]
    if any(not device_id.strip() for device_id in device_ids):
        parser.error("--device-id không được để trống")

    parameters = pika.URLParameters(os.getenv("AMQP_URL", DEFAULT_AMQP_URL))
    connection = pika.BlockingConnection(parameters)
    try:
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE, durable=True)
        channel.confirm_delivery()
        print(f"Dang gui du lieu moi 3 giay cho {', '.join(device_ids)}. Nhan Ctrl+C de dung.")
        round_number = 0
        try:
            while args.count == 0 or round_number < args.count:
                for device_id in device_ids:
                    payload = {
                        "device_id": device_id.strip(),
                        "temperature": round(random.uniform(20, 40), 1),
                        "humidity": round(random.uniform(30, 80), 1),
                        "sent_at": datetime.now(timezone.utc).isoformat(),
                    }
                    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                    channel.basic_publish(
                        exchange="",
                        routing_key=QUEUE,
                        body=body,
                        properties=pika.BasicProperties(
                            content_type="application/json", delivery_mode=2
                        ),
                        mandatory=True,
                    )
                    print(f"Da gui: {body.decode('utf-8')}", flush=True)
                round_number += 1
                if args.count == 0 or round_number < args.count:
                    time.sleep(3)
        except KeyboardInterrupt:
            print("Da dung sensor producer.")
    finally:
        if connection.is_open:
            connection.close()


if __name__ == "__main__":
    main()
