# 1. Tải môi trường Python siêu nhẹ
FROM python:3.9-slim

# 2. Tạo thư mục làm việc trong Container
WORKDIR /app

# 3. Copy file requirements và cài đặt thư viện
COPY requirements.txt .
RUN pip install -r requirements.txt

# 4. Copy mã nguồn web (app.py) vào Container
COPY . .

# 5. Mở cổng 5000
EXPOSE 5000

# 6. Khởi chạy ứng dụng
CMD ["python", "app.py"]