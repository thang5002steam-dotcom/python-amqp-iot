"""Tạo và kiểm tra dữ liệu của các bài thực hành; không phụ thuộc RabbitMQ."""

import random
from datetime import datetime, timezone
from math import isfinite


ALERT_LEVELS = ("info", "warning", "critical")


def student_message(student_id, student_name, greeting):
    student_id = student_id.strip()
    student_name = student_name.strip()
    greeting = greeting.strip()
    if not all((student_id, student_name, greeting)):
        raise ValueError("Mã sinh viên, họ tên và lời chào không được để trống")
    return f"{greeting} - {student_id} - {student_name}"


def sensor_reading(device_id, *, rng=None, sent_at=None):
    """Sinh một bản ghi telemetry với thời gian UTC theo ISO 8601."""
    device_id = device_id.strip()
    if not device_id:
        raise ValueError("device_id không được để trống")
    rng = rng or random
    sent_at = sent_at or datetime.now(timezone.utc)
    return {
        "device_id": device_id,
        "temperature": round(rng.uniform(20, 40), 1),
        "humidity": round(rng.uniform(30, 80), 1),
        "sent_at": sent_at.isoformat(),
    }


def validate_sensor_reading(payload):
    """Trả về các trường cần hiển thị hoặc báo lỗi nếu JSON không hợp lệ."""
    if not isinstance(payload, dict):
        raise ValueError("Payload phải là một JSON object")
    device_id = payload.get("device_id")
    temperature = payload.get("temperature")
    humidity = payload.get("humidity")
    if not isinstance(device_id, str) or not device_id.strip():
        raise ValueError("device_id phải là chuỗi không rỗng")
    if isinstance(temperature, bool) or not isinstance(temperature, (int, float)):
        raise ValueError("temperature phải là số")
    if isinstance(humidity, bool) or not isinstance(humidity, (int, float)):
        raise ValueError("humidity phải là số")
    if not isfinite(temperature) or not isfinite(humidity):
        raise ValueError("temperature và humidity phải là số hữu hạn")
    if not -100 <= temperature <= 150:
        raise ValueError("temperature nằm ngoài phạm vi hợp lý")
    if not 0 <= humidity <= 100:
        raise ValueError("humidity phải nằm trong khoảng 0–100")
    return device_id.strip(), temperature, humidity


def sensor_warnings(temperature, humidity):
    warnings = []
    if temperature > 35:
        warnings.append("CANH BAO: Nhiet do cao")
    if humidity < 40:
        warnings.append("CANH BAO: Do am thap")
    return warnings
