# Thực hành Python AMQP với RabbitMQ

Project gồm **đúng 7 chương trình Python và README này**. Ba bài thực hành lần lượt gửi lời chào qua queue, mô phỏng dữ liệu cảm biến IoT và phân luồng cảnh báo bằng `direct exchange`. Mỗi chương trình là một file độc lập; ngoài thư viện `pika`, không cần module Python nào khác của project.

## 1. File nộp bài

| Bài | File | Chức năng |
| --- | --- | --- |
| 1 | `producer_bai1.py` | Gửi lời chào, mã sinh viên và họ tên. |
| 1 | `consumer_bai1.py` | Nhận lời chào, in nội dung và thời điểm nhận. |
| 2 | `sensor_producer_bai2.py` | Gửi dữ liệu JSON của một hoặc nhiều cảm biến. |
| 2 | `monitor_consumer_bai2.py` | Nhận dữ liệu và cảnh báo theo ngưỡng. |
| 3 | `alert_producer_bai3.py` | Gửi các mức cảnh báo theo routing key. |
| 3 | `warning_consumer_bai3.py` | Chỉ nhận cảnh báo `warning`. |
| 3 | `critical_consumer_bai3.py` | Chỉ nhận cảnh báo `critical`. |
| — | `README.md` | Broker sử dụng, cách chạy và kết quả đạt được. |

## 2. Broker sử dụng

- Broker: **RabbitMQ**, giao thức **AMQP 0-9-1**; ứng dụng Python kết nối qua thư viện **Pika**.
- Môi trường đã dùng để kiểm tra: RabbitMQ **4.3.6**, Erlang/OTP **27.3.4.18** trên máy cục bộ.
- Kết nối mặc định: `localhost:5672`, virtual host `/`, tài khoản `guest`, mật khẩu `guest`.
- Nếu dùng broker khác, đặt biến môi trường `AMQP_URL` trong **mỗi terminal** chạy chương trình. Ví dụ PowerShell: `$env:AMQP_URL = "amqp://user:password@host:5672/%2F"`; CMD: `set AMQP_URL=amqp://user:password@host:5672/%2F`. `%2F` biểu diễn virtual host `/`. Tài khoản và mật khẩu có ký tự đặc biệt cần mã hóa URL.

| Bài | Exchange | Routing key | Queue |
| --- | --- | --- | --- |
| 1 | Default exchange (`""`) | `iot_lab_queue` | `iot_lab_queue` |
| 2 | Default exchange (`""`) | `sensor_data_queue` | `sensor_data_queue` |
| 3 | `iot_alert_exchange` (direct) | `warning` | `warning_queue` |
| 3 | `iot_alert_exchange` (direct) | `critical` | `critical_queue` |

Routing key `info` của bài 3 không được bind với queue nào trong bài này. Queue và exchange được khai báo `durable`; message gửi ở chế độ `persistent`. Consumer xác nhận xử lý bằng `ack`.

## 3. Chuẩn bị

1. Cài Python 3.9 trở lên và khởi động RabbitMQ. Broker phải lắng nghe ở `localhost:5672` nếu dùng cấu hình mặc định. Có thể dùng RabbitMQ cài trên máy hoặc container RabbitMQ; các file nộp bài không phụ thuộc Docker.
2. Mở CMD hoặc PowerShell tại thư mục chứa 8 file, tạo môi trường Python và cài `pika`:

   ```text
   py -3 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install pika
   ```

3. Trong các lệnh bên dưới, luôn gọi `.\.venv\Scripts\python.exe` để dùng đúng Python đã cài `pika`. Nếu `.venv` đã tồn tại, chỉ cần chạy lại lệnh cài `pika` khi thiếu thư viện. Trên macOS/Linux, dùng `python3 -m venv .venv`, `./.venv/bin/python -m pip install pika`, rồi thay đường dẫn Python trong từng lệnh.

## 4. Bài 1 — Gửi và nhận lời chào

**Terminal 1**, chạy consumer trước:

```text
.\.venv\Scripts\python.exe consumer_bai1.py
```

**Terminal 2**, thay mã sinh viên và họ tên mẫu bằng thông tin của bạn:

```text
.\.venv\Scripts\python.exe producer_bai1.py --student-id B21xxxx --student-name "Nguyen Van A"
```

Muốn gửi ba message để kiểm tra đủ số lượng:

```text
.\.venv\Scripts\python.exe producer_bai1.py --student-id B21xxxx --student-name "Nguyen Van A" --count 3
```

Producer in `Da gui 1/3`, `Da gui 2/3`, `Da gui 3/3`. Consumer in mỗi message cùng giờ nhận theo đồng hồ máy, ví dụ:

```text
Da nhan message: Xin chao tu ung dung Python AMQP - B21xxxx - Nguyen Van A
Thoi gian nhan: 14:05:21
```

Hai tham số `--student-id`, `--student-name` là bắt buộc; `--count` mặc định là 1. Có thể đổi lời chào bằng `--greeting "Loi chao cua toi"`. Nhấn `Ctrl+C` để dừng consumer.

## 5. Bài 2 — Dữ liệu cảm biến IoT

**Terminal 1**, chạy monitor:

```text
.\.venv\Scripts\python.exe monitor_consumer_bai2.py
```

**Terminal 2**, chạy một cảm biến `sensor01` liên tục:

```text
.\.venv\Scripts\python.exe sensor_producer_bai2.py
```

Để chạy hai cảm biến trong đúng hai lượt rồi tự dừng:

```text
.\.venv\Scripts\python.exe sensor_producer_bai2.py --device-id sensor01 --device-id sensor02 --count 2
```

Mỗi lượt gửi một message cho từng cảm biến; ví dụ trên gửi **4 JSON** và chờ **3 giây giữa hai lượt**. `--device-id` có thể lặp lại; `--count 0` là chạy liên tục. Message có dạng:

```json
{"device_id":"sensor01","temperature":36.4,"humidity":38.9,"sent_at":"2026-01-01T00:00:00+00:00"}
```

Nhiệt độ được sinh ngẫu nhiên trong khoảng 20–40°C, độ ẩm 30–80%; `sent_at` dùng giờ UTC. Monitor in mã cảm biến, nhiệt độ và độ ẩm. Hai điều kiện cảnh báo độc lập:

| Điều kiện | Kết quả in ra |
| --- | --- |
| `temperature > 35` | `CANH BAO: Nhiet do cao` |
| `humidity < 40` | `CANH BAO: Do am thap` |

Với 36.4°C và 38.9%, cả hai dòng cảnh báo xuất hiện. Đúng bằng 35°C hoặc 40% không phát cảnh báo. JSON không hợp lệ được thông báo và bỏ qua để consumer tiếp tục xử lý. Nhấn `Ctrl+C` để dừng chương trình chạy liên tục.

## 6. Bài 3 — Direct exchange và routing key

**Terminal 1**, chạy consumer cho cảnh báo `warning`:

```text
.\.venv\Scripts\python.exe warning_consumer_bai3.py
```

**Terminal 2**, chạy consumer cho cảnh báo `critical`:

```text
.\.venv\Scripts\python.exe critical_consumer_bai3.py
```

**Terminal 3**, gửi lần lượt ba message mẫu có routing key `info`, `warning`, `critical`:

```text
.\.venv\Scripts\python.exe alert_producer_bai3.py
```

Kết quả ở warning consumer:

```text
[warning_queue] Da nhan: Nhiet do phong may vuot nguong warning
```

Kết quả ở critical consumer:

```text
[critical_queue] Da nhan: Cam bien kho lanh mat ket noi critical
```

Message `info` không xuất hiện ở hai consumer vì không có binding `info`. Có thể gửi một cảnh báo tùy chọn:

```text
.\.venv\Scripts\python.exe alert_producer_bai3.py --level warning --message "Nhiet do phong may vuot nguong"
```

`--level` chỉ nhận `info`, `warning`, `critical`; `--message` phải đi kèm `--level`. **Lần đầu hãy chạy cả hai consumer trước producer** để tạo queue và binding. Nếu producer gửi khi chưa có binding phù hợp, message đó không được lưu vào queue. Nhấn `Ctrl+C` để dừng consumer.

## 7. Kết quả đạt được

Các bài đã được kiểm tra đầu cuối với RabbitMQ cục bộ:

| Bài | Cách kiểm tra | Kết quả |
| --- | --- | --- |
| 1 | Gửi ba lời chào vào `iot_lab_queue`. | Consumer nhận **3/3** message, đúng nội dung và có thời điểm nhận; queue không còn message chờ. |
| 2 | Chạy hai cảm biến trong hai lượt. Thử thêm các giá trị 36.4°C/38.9%, 35°C/40% và JSON lỗi. | Nhận **4/4** JSON từ producer; hiện cả hai cảnh báo khi vượt ngưỡng, không cảnh báo tại ngưỡng, bỏ qua JSON lỗi và tiếp tục nhận. |
| 3 | Gửi bộ ba cảnh báo mẫu và thêm các cảnh báo riêng. | `warning_queue` chỉ nhận `warning`, `critical_queue` chỉ nhận `critical`; không nhận chéo, `info` không vào hai queue. |

Các số **3/3** và **4/4** là kết quả của ca kiểm tra trên, không phải số message cố định mỗi lần chạy. Dữ liệu cảm biến được tạo ngẫu nhiên nên cảnh báo có thể khác giữa các lần chạy.

## 8. Lỗi thường gặp

| Hiện tượng | Cách xử lý |
| --- | --- |
| `ModuleNotFoundError: No module named 'pika'` | Chạy `.\.venv\Scripts\python.exe -m pip install pika` và dùng chính Python trong `.venv` để chạy script. |
| Không kết nối được RabbitMQ | Kiểm tra broker đang chạy, cổng 5672 và biến `AMQP_URL`. |
| Producer bài 1 báo thiếu tham số | Cung cấp cả `--student-id` và `--student-name`; đặt họ tên có khoảng trắng trong dấu nháy kép. |
| Bài 2 không hiện cảnh báo | Dữ liệu ngẫu nhiên; cảnh báo chỉ hiện khi vượt điều kiện ở mục 5. |
| Bài 3 gửi được nhưng consumer không nhận | Chạy consumer trước để tạo binding; kiểm tra routing key và virtual host. `info` vốn không có consumer trong bài này. |
| `PRECONDITION_FAILED` | Broker có queue hoặc exchange trùng tên nhưng khác thuộc tính; kiểm tra tài nguyên cũ hoặc dùng virtual host mới. |
