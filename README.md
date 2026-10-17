# Thực hành Python AMQP với RabbitMQ – mô phỏng IoT

Project triển khai ba bài thực hành: gửi lời chào qua queue, gửi dữ liệu cảm biến IoT và phân luồng cảnh báo bằng `direct exchange`. Bảy chương trình theo yêu cầu nộp bài nằm ở thư mục gốc. Các lệnh dưới đây chạy từ chính thư mục `python-amqp-iot`.

## 1. Danh sách file nộp bài

| Bài | File | Vai trò |
| --- | --- | --- |
| 1 | `producer_bai1.py` | Gửi lời chào kèm mã sinh viên và họ tên. |
| 1 | `consumer_bai1.py` | Nhận lời chào và in thời điểm nhận. |
| 2 | `sensor_producer_bai2.py` | Tạo dữ liệu JSON cho một hoặc nhiều cảm biến, gửi mỗi 3 giây. |
| 2 | `monitor_consumer_bai2.py` | Hiển thị dữ liệu và phát cảnh báo theo ngưỡng. |
| 3 | `alert_producer_bai3.py` | Gửi cảnh báo `info`, `warning`, `critical` theo routing key. |
| 3 | `warning_consumer_bai3.py` | Chỉ nhận cảnh báo `warning`. |
| 3 | `critical_consumer_bai3.py` | Chỉ nhận cảnh báo `critical`. |

**Nộp kèm** `README.md` này và các file hỗ trợ `amqp_common.py`, `message_utils.py`, `requirements.txt`. Bảy chương trình import hai module hỗ trợ nên sẽ không chạy được nếu thiếu chúng. `compose.yaml` giúp tạo broker bằng Docker; `tests/` chứa kiểm tra logic. Không cần nộp `.venv/`, `__pycache__/` hoặc thông tin đăng nhập riêng.

## 2. Broker sử dụng và sơ đồ truyền tin

Project dùng **RabbitMQ** theo giao thức **AMQP 0-9-1**, thư viện Python **Pika**. Các bài đã được kiểm tra đầu cuối với **RabbitMQ 4.3.6**, **Erlang/OTP 27.3.4.18** chạy trên máy cục bộ. Cấu hình kết nối mặc định:

| Thông số | Giá trị mặc định |
| --- | --- |
| Host | `localhost` |
| Cổng AMQP | `5672` |
| Virtual host | `/` |
| Tài khoản | `guest` |
| Mật khẩu | `guest` |

Tài khoản `guest` dùng cho broker cục bộ. Nếu dùng broker khác, xem mục 3 để đổi cấu hình. Có thể dùng `compose.yaml` để chạy image `rabbitmq:4-management`; image này cung cấp giao diện quản trị tại <http://localhost:15672>, còn ứng dụng Python vẫn dùng cổng `5672`.

| Bài | Đường truyền | Queue nhận |
| --- | --- | --- |
| 1 | Producer → default exchange (`""`) → routing key `iot_lab_queue` | `iot_lab_queue` |
| 2 | Sensor producer → default exchange (`""`) → routing key `sensor_data_queue` | `sensor_data_queue` |
| 3 | Alert producer → `iot_alert_exchange` (`direct`) → routing key `warning` | `warning_queue` |
| 3 | Alert producer → `iot_alert_exchange` (`direct`) → routing key `critical` | `critical_queue` |

Routing key `info` chưa được bind với queue nào trong bài 3, nên hai consumer bài 3 không nhận message này. Queue và exchange được khai báo `durable`; message được gửi ở chế độ `persistent`. Consumer xác nhận xử lý bằng `ack`. Message sai định dạng được loại khỏi queue bằng `nack(requeue=False)` để không lặp vô hạn.

## 3. Chuẩn bị môi trường

Yêu cầu Python 3.9 trở lên, RabbitMQ đang lắng nghe ở cổng 5672, và thư viện `pika` trong `requirements.txt`.

**Windows CMD hoặc PowerShell** — chạy một lần trong thư mục project:

```text
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Nếu đã có `.venv`, chỉ cần chạy dòng cài thư viện. Trong toàn bộ ví dụ Windows bên dưới, gọi trực tiếp `.\.venv\Scripts\python.exe` để chắc chắn chương trình dùng đúng Python đã cài `pika`.

**macOS/Linux**:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
```

Nếu đã cài Docker Desktop/Docker Compose và muốn tạo broker cục bộ:

```text
docker compose up -d
```

Đợi RabbitMQ sẵn sàng rồi mới chạy các chương trình. Với Docker Compose, có thể kiểm tra bằng `docker compose ps` và mở <http://localhost:15672> (`guest` / `guest`). Sau khi làm xong, chạy `docker compose down` để dừng container. Nếu dùng RabbitMQ đã cài trên máy, chỉ cần bảo đảm broker đang chạy; không cần Docker.

### Đổi broker hoặc tài khoản

Mọi chương trình dùng chung cấu hình trong `amqp_common.py`. Có thể đặt biến môi trường trong **từng terminal** trước khi chạy:

| Biến | Mặc định | Mục đích |
| --- | --- | --- |
| `RABBITMQ_HOST` | `localhost` | Địa chỉ broker. |
| `RABBITMQ_PORT` | `5672` | Cổng AMQP. |
| `RABBITMQ_USER` | `guest` | Tên đăng nhập. |
| `RABBITMQ_PASSWORD` | `guest` | Mật khẩu. |
| `RABBITMQ_VHOST` | `/` | Virtual host. |
| `AMQP_URL` | Không đặt | URL kết nối đầy đủ; được ưu tiên hơn các biến trên. |

Ví dụ PowerShell:

```powershell
$env:RABBITMQ_HOST = "localhost"
$env:RABBITMQ_PORT = "5672"
$env:RABBITMQ_VHOST = "/"
```

Ví dụ CMD: `set RABBITMQ_HOST=localhost`. File `.env.example` chỉ là mẫu; chương trình **không tự đọc** file `.env`. Không đưa mật khẩu thật vào Git.

## 4. Bài 1 – Gửi và nhận lời chào

Mục tiêu: producer gửi chuỗi gồm lời chào, mã sinh viên và họ tên vào `iot_lab_queue`; consumer nhận chuỗi và in giờ nhận theo đồng hồ máy.

1. Mở **terminal 1** tại thư mục project và chạy consumer:

   ```text
   .\.venv\Scripts\python.exe consumer_bai1.py
   ```

2. Mở **terminal 2** tại cùng thư mục và chạy producer. Thay thông tin mẫu bằng thông tin của bạn:

   ```text
   .\.venv\Scripts\python.exe producer_bai1.py --student-id B21xxxx --student-name "Nguyen Van A"
   ```

3. Muốn thử gửi ba message liên tiếp:

   ```text
   .\.venv\Scripts\python.exe producer_bai1.py --student-id B21xxxx --student-name "Nguyen Van A" --count 3
   ```

Producer in `Da gui 1/3`, `Da gui 2/3`, `Da gui 3/3`. Consumer in nội dung và thời điểm nhận, ví dụ:

```text
Da nhan message: Xin chao tu ung dung Python AMQP - B21xxxx - Nguyen Van A
Thoi gian nhan: 14:05:21
```

`--student-id` và `--student-name` là bắt buộc; `--count` mặc định là `1`. Có thể đổi lời chào bằng `--greeting "Loi chao cua toi"`. Nhấn `Ctrl+C` ở terminal consumer để dừng.

## 5. Bài 2 – Mô phỏng và giám sát cảm biến

Mục tiêu: producer tạo các JSON có `device_id`, `temperature`, `humidity`, `sent_at` rồi gửi vào `sensor_data_queue`. Nhiệt độ được sinh trong khoảng 20–40°C, độ ẩm 30–80%. `sent_at` là thời điểm gửi theo UTC.

1. **Terminal 1**: chạy chương trình giám sát:

   ```text
   .\.venv\Scripts\python.exe monitor_consumer_bai2.py
   ```

2. **Terminal 2**: chạy một cảm biến liên tục:

   ```text
   .\.venv\Scripts\python.exe sensor_producer_bai2.py
   ```

   Mặc định cảm biến có mã `sensor01`. Producer gửi một lượt rồi đợi **3 giây** trước lượt tiếp theo. Nhấn `Ctrl+C` để dừng.

3. Để mô phỏng hai cảm biến trong đúng hai lượt rồi tự dừng:

   ```text
   .\.venv\Scripts\python.exe sensor_producer_bai2.py --device-id sensor01 --device-id sensor02 --count 2
   ```

   Mỗi lượt gửi một JSON cho từng `device_id`, nên ví dụ trên gửi tổng cộng **4 message**. Có thể lặp thêm `--device-id sensor03`; `--count 0` nghĩa là chạy liên tục.

Một payload mẫu:

```json
{"device_id":"sensor01","temperature":36.4,"humidity":38.9,"sent_at":"2026-01-01T00:00:00+00:00"}
```

Consumer hiển thị mã cảm biến, nhiệt độ, độ ẩm, và kiểm tra **hai điều kiện độc lập**:

| Điều kiện | Dòng cảnh báo |
| --- | --- |
| `temperature > 35` | `CANH BAO: Nhiet do cao` |
| `humidity < 40` | `CANH BAO: Do am thap` |

Với payload mẫu trên, consumer in cả hai cảnh báo. Giá trị đúng bằng 35°C hoặc 40% **không** kích hoạt cảnh báo. Dữ liệu ngẫu nhiên nên một lần chạy thực tế có thể có không, một hoặc hai cảnh báo. JSON sai, thiếu trường hoặc giá trị không hợp lệ được thông báo và bỏ qua; consumer tiếp tục nhận message sau.

## 6. Bài 3 – Phân luồng cảnh báo bằng direct exchange

Mục tiêu: producer gửi ba mức `info`, `warning`, `critical` vào exchange `iot_alert_exchange`. Queue `warning_queue` bind với routing key `warning`, queue `critical_queue` bind với routing key `critical`.

1. **Terminal 1**: chạy warning consumer:

   ```text
   .\.venv\Scripts\python.exe warning_consumer_bai3.py
   ```

2. **Terminal 2**: chạy critical consumer:

   ```text
   .\.venv\Scripts\python.exe critical_consumer_bai3.py
   ```

3. **Terminal 3**: gửi bộ ba cảnh báo mẫu:

   ```text
   .\.venv\Scripts\python.exe alert_producer_bai3.py
   ```

Producer in ba dòng `Da gui [info]`, `Da gui [warning]`, `Da gui [critical]`. Warning consumer chỉ in:

```text
[warning_queue] Da nhan: Nhiet do phong may vuot nguong warning
```

Critical consumer chỉ in:

```text
[critical_queue] Da nhan: Cam bien kho lanh mat ket noi critical
```

Message `info` không xuất hiện ở hai consumer vì không có binding cho key này. Có thể gửi một cảnh báo tùy chọn:

```text
.\.venv\Scripts\python.exe alert_producer_bai3.py --level warning --message "Nhiet do phong may vuot nguong"
```

`--level` chỉ nhận `info`, `warning`, `critical`. Nếu dùng `--message`, phải kèm `--level`. Ở lần chạy đầu, hãy bật **hai consumer trước producer** để tạo queue và binding; message gửi đến exchange khi chưa có binding phù hợp sẽ không chờ trong queue. Sau khi binding đã tồn tại, có thể dừng consumer và chạy lại để đọc các message đang chờ. Nhấn `Ctrl+C` để dừng mỗi consumer.

## 7. Kết quả đạt được và cách kiểm tra lại

Project đã được chạy kiểm tra đầu cuối với broker RabbitMQ cục bộ nêu ở mục 2:

| Bài | Ca kiểm tra thực tế | Kết quả |
| --- | --- | --- |
| 1 | Gửi 3 lời chào qua `iot_lab_queue`. | Consumer nhận đủ **3/3**, in đúng nội dung và thời điểm; queue không còn message chờ sau khi xử lý. |
| 2 | Chạy `sensor01` và `sensor02` trong 2 lượt, cách nhau 3 giây. | Consumer nhận đủ **4/4 JSON**. Bản ghi 36.4°C/38.9% hiện cả hai cảnh báo; 35°C/40% không cảnh báo. JSON lỗi được bỏ qua và luồng nhận tiếp tục. |
| 3 | Gửi mẫu `info`, `warning`, `critical` và thử thêm từng loại. | `warning_queue` nhận đúng cảnh báo `warning`, `critical_queue` nhận đúng `critical`; không nhận chéo. `info` không vào hai queue. Sau các ca thử, hai queue không còn message chờ. |

Các con số trên là kết quả kiểm tra của project, không phải số cố định ở mọi lần chạy. Để tự kiểm tra lại, chạy broker, mở các terminal theo thứ tự tại mục 4–6, đối chiếu đầu ra producer và consumer. Nếu dùng Docker Compose, giao diện quản trị có thể cho thấy queue, exchange, binding và số message đang chờ.

Kiểm tra riêng logic tạo/kiểm tra payload, không cần broker:

```text
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Bộ test hiện có **4 ca** cho lời chào, cấu trúc telemetry, ngưỡng cảnh báo và dữ liệu sai. Lệnh tương ứng trên macOS/Linux: `./.venv/bin/python -m unittest discover -s tests -v`.

## 8. Lỗi thường gặp

| Hiện tượng | Cách xử lý |
| --- | --- |
| `ModuleNotFoundError: No module named 'pika'` | Cài `pika` bằng `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`, rồi dùng chính Python trong `.venv` để chạy script. |
| Không kết nối được broker | Kiểm tra RabbitMQ đã khởi động, cổng 5672, host, virtual host và tài khoản. Với Docker, kiểm tra `docker compose ps`. |
| Producer bài 1 báo thiếu tham số | Thêm cả `--student-id` và `--student-name`; họ tên có khoảng trắng cần đặt trong dấu nháy kép. |
| Bài 2 không thấy cảnh báo | Giá trị sinh ngẫu nhiên; chỉ hiện cảnh báo khi vượt đúng ngưỡng ở mục 5. |
| Bài 3 producer báo đã gửi nhưng consumer không nhận | Ở lần đầu cần chạy hai consumer để tạo binding, dùng đúng routing key và cùng virtual host. `info` không có consumer trong bài này. |
| `PRECONDITION_FAILED` khi khai báo queue/exchange | Trên broker đã có tài nguyên trùng tên nhưng khác thuộc tính (chẳng hạn queue cũ không `durable`). Kiểm tra tài nguyên hiện có hoặc dùng virtual host mới. |

## 9. Cấu trúc project

```text
python-amqp-iot/
├── README.md
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
