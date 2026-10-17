# Thực hành Python với AMQP và RabbitMQ

Project này triển khai đầy đủ ba bài thực hành trong tài liệu: gửi lời chào qua queue, mô phỏng dữ liệu cảm biến IoT và điều phối cảnh báo bằng direct exchange. Mỗi bài có các chương trình độc lập đúng tên file yêu cầu nộp. Các file `amqp_common.py` và `message_utils.py` chứa cấu hình và logic dùng chung.

## 1. Yêu cầu môi trường

- Python 3.9 trở lên.
- RabbitMQ đang chạy và mở cổng AMQP 5672. Có thể dùng broker đã cài trên máy, broker của lớp hoặc Docker Compose.
- Thư viện Python `pika` được cài từ `requirements.txt`.

Tạo môi trường ảo và cài thư viện trong thư mục project:

**Windows PowerShell**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

**macOS/Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Nếu đã có broker của lớp, dùng thông tin kết nối do giảng viên cung cấp. Nếu đã có Docker Compose, có thể khởi động một broker cục bộ:

```bash
docker compose up -d
```

RabbitMQ Management UI sau đó ở <http://localhost:15672> (tài khoản mặc định của container: `guest` / `guest`). Các chương trình Python kết nối cổng 5672. Khi xong, dừng container bằng `docker compose down`.

## 2. Cấu hình kết nối

Mặc định project kết nối `localhost:5672`, virtual host `/`, người dùng `guest`, mật khẩu `guest`. Tài khoản `guest` thường chỉ dùng được khi kết nối cục bộ. Với broker của lớp, đặt các biến môi trường sau trước khi chạy chương trình:

| Biến | Mặc định | Ý nghĩa |
| --- | --- | --- |
| `RABBITMQ_HOST` | `localhost` | Địa chỉ broker |
| `RABBITMQ_PORT` | `5672` | Cổng AMQP |
| `RABBITMQ_USER` | `guest` | Tên đăng nhập |
| `RABBITMQ_PASSWORD` | `guest` | Mật khẩu |
| `RABBITMQ_VHOST` | `/` | Virtual host |
| `AMQP_URL` | Không có | URL đầy đủ; khi có sẽ ưu tiên hơn mọi biến trên |

Ví dụ cho PowerShell:

```powershell
$env:RABBITMQ_HOST = "localhost"
$env:RABBITMQ_USER = "guest"
$env:RABBITMQ_PASSWORD = "guest"
```

Ví dụ cho macOS/Linux:

```bash
export RABBITMQ_HOST=localhost
export RABBITMQ_USER=guest
export RABBITMQ_PASSWORD=guest
```

Có thể dùng một URL thay thế, ví dụ `AMQP_URL=amqp://user:password@broker.example:5672/%2F`. Nếu mật khẩu có ký tự đặc biệt, cần mã hóa theo quy tắc URL. File `.env.example` chỉ là mẫu tham khảo; các script đọc biến môi trường của terminal và **không tự nạp** file `.env`.

## 3. Bài 1: Producer → queue → consumer

Queue sử dụng: `iot_lab_queue`. Mở **terminal 1** và chạy consumer:

```bash
python consumer_bai1.py
```

Mở **terminal 2** tại cùng thư mục project và gửi lời chào. Thay mã và họ tên bằng thông tin của bạn:

```bash
python producer_bai1.py --student-id B21xxxx --student-name "Nguyen Van A"
```

Để gửi nhiều message liên tiếp:

```bash
python producer_bai1.py --student-id B21xxxx --student-name "Nguyen Van A" --count 3
```

Kết quả dự kiến ở terminal consumer:

```text
Da nhan message: Xin chao tu ung dung Python AMQP - B21xxxx - Nguyen Van A
Thoi gian nhan: 14:05:21
```

Thời gian phụ thuộc đồng hồ máy nhận. Consumer tiếp tục lắng nghe cho đến khi nhấn `Ctrl+C`.

## 4. Bài 2: Telemetry cảm biến IoT

Queue sử dụng: `sensor_data_queue`. Mở **terminal 1**:

```bash
python monitor_consumer_bai2.py
```

Mở **terminal 2**. Producer gửi một bản ghi JSON mỗi 3 giây:

```bash
python sensor_producer_bai2.py
```

Muốn mô phỏng ba cảm biến, mỗi lượt sẽ gửi ba bản ghi rồi đợi 3 giây trước lượt tiếp theo:

```bash
python sensor_producer_bai2.py --device-id sensor01 --device-id sensor02 --device-id sensor03
```

Muốn chạy đúng hai lượt rồi tự dừng:

```bash
python sensor_producer_bai2.py --device-id sensor01 --device-id sensor02 --count 2
```

Payload mẫu:

```json
{
  "device_id": "sensor01",
  "temperature": 36.4,
  "humidity": 38.9,
  "sent_at": "2026-01-01T00:00:00+00:00"
}
```

`temperature` và `humidity` được sinh ngẫu nhiên. `sent_at` là thời gian gửi theo UTC. Consumer hiển thị mã thiết bị, nhiệt độ, độ ẩm và cảnh báo khi **nhiệt độ lớn hơn 35** hoặc **độ ẩm nhỏ hơn 40**:

```text
Device: sensor01
Temperature: 36.4
Humidity: 38.9
CANH BAO: Nhiet do cao
CANH BAO: Do am thap
```

Các giá trị đúng bằng 35 hoặc 40 không kích hoạt cảnh báo. Message sai JSON hoặc thiếu trường sẽ được báo lỗi và loại khỏi queue để consumer tiếp tục xử lý message sau.

## 5. Bài 3: Direct exchange và routing key

Exchange: `iot_alert_exchange`, loại `direct`. Hai queue nhận cảnh báo:

| Queue | Routing key được bind | Nội dung nhận |
| --- | --- | --- |
| `warning_queue` | `warning` | Chỉ cảnh báo warning |
| `critical_queue` | `critical` | Chỉ cảnh báo critical |

Mở **terminal 1** và **terminal 2** trước để tạo queue và binding:

```bash
python warning_consumer_bai3.py
```

```bash
python critical_consumer_bai3.py
```

Mở **terminal 3** và gửi ba message mẫu với routing key `info`, `warning`, `critical`:

```bash
python alert_producer_bai3.py
```

Kết quả dự kiến:

```text
# Terminal warning
[warning_queue] Da nhan: Nhiet do phong may vuot nguong warning

# Terminal critical
[critical_queue] Da nhan: Cam bien kho lanh mat ket noi critical
```

Message `info` không được hai consumer này nhận vì không có queue nào bind routing key `info`. Có thể gửi riêng một cảnh báo:

```bash
python alert_producer_bai3.py --level warning --message "Nhiet do phong may vuot nguong"
```

Với direct exchange, message gửi **trước khi queue/binding tồn tại** sẽ không nằm chờ cho consumer tương ứng. Vì vậy hãy chạy hai consumer trước khi chạy producer lần đầu. Sau khi queue và binding đã tồn tại, có thể dừng consumer; message mới vẫn được lưu trong queue bền vững để nhận sau.

## 6. Cấu trúc project

```text
python-amqp-iot/
├── producer_bai1.py
├── consumer_bai1.py
├── sensor_producer_bai2.py
├── monitor_consumer_bai2.py
├── alert_producer_bai3.py
├── warning_consumer_bai3.py
├── critical_consumer_bai3.py
├── amqp_common.py
├── message_utils.py
├── requirements.txt
├── compose.yaml
├── .env.example
└── tests/
    └── test_message_utils.py
```

Producer khai báo queue/exchange bền vững và gửi message ở chế độ persistent. Consumer xác nhận (`ack`) sau khi xử lý thành công. Nếu payload không hợp lệ, consumer loại message đó (`nack`, không đưa lại vào queue) để tránh xử lý lặp vô hạn.

## 7. Kiểm tra project

Chạy các kiểm tra logic không cần broker:

```bash
python -m unittest discover -s tests -v
```

Để kiểm tra luồng AMQP thực tế, bật RabbitMQ rồi chạy ba cặp bài theo mục 3–5. Có thể mở Management UI để quan sát queue, exchange, binding và số message đang chờ.

## 8. Xử lý lỗi thường gặp

- **Không kết nối được broker:** kiểm tra RabbitMQ đang chạy, host/cổng, firewall, virtual host và thông tin đăng nhập. Với Docker, chạy `docker compose ps`.
- **`ModuleNotFoundError: No module named 'pika'`:** kích hoạt đúng môi trường ảo và chạy lại `python -m pip install -r requirements.txt`.
- **Lỗi `PRECONDITION_FAILED` khi khai báo queue/exchange:** broker đang có queue/exchange trùng tên nhưng khác thuộc tính (ví dụ queue cũ không durable). Dùng virtual host mới hoặc xử lý tài nguyên cũ sau khi đã lưu dữ liệu cần thiết.
- **Bài 3 gửi được nhưng consumer không nhận:** khởi chạy consumer để tạo binding trước khi gửi; kiểm tra đúng routing key `warning` hoặc `critical` và cùng virtual host.
- **Không có cảnh báo ở bài 2:** dữ liệu được sinh ngẫu nhiên; tiếp tục chạy để thấy giá trị vượt ngưỡng.
