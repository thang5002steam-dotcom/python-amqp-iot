import random
import unittest
from datetime import datetime, timezone

from message_utils import sensor_reading, sensor_warnings, student_message, validate_sensor_reading


class MessageUtilsTests(unittest.TestCase):
    def test_student_message_has_all_required_parts(self):
        self.assertEqual(
            student_message(" B21xxxx ", " Nguyen Van A ", " Xin chao "),
            "Xin chao - B21xxxx - Nguyen Van A",
        )

    def test_sensor_reading_contains_valid_json_fields(self):
        reading = sensor_reading(
            "sensor01", rng=random.Random(7), sent_at=datetime(2026, 1, 1, tzinfo=timezone.utc)
        )
        self.assertEqual(reading["device_id"], "sensor01")
        self.assertEqual(reading["sent_at"], "2026-01-01T00:00:00+00:00")
        self.assertTrue(20 <= reading["temperature"] <= 40)
        self.assertTrue(30 <= reading["humidity"] <= 80)
        self.assertEqual(
            validate_sensor_reading(reading),
            ("sensor01", reading["temperature"], reading["humidity"]),
        )

    def test_thresholds_are_strict(self):
        self.assertEqual(sensor_warnings(35, 40), [])
        self.assertEqual(
            sensor_warnings(36.4, 38.9),
            ["CANH BAO: Nhiet do cao", "CANH BAO: Do am thap"],
        )

    def test_invalid_sensor_payload_is_rejected(self):
        for payload in ({"device_id": "s", "temperature": True, "humidity": 50},
                        {"device_id": "s", "temperature": 30, "humidity": 101},
                        {"device_id": "s", "temperature": float("nan"), "humidity": 50},
                        {"device_id": "", "temperature": 30, "humidity": 50}):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                validate_sensor_reading(payload)


if __name__ == "__main__":
    unittest.main()
