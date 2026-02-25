# 🛠️ Development Setup Guide

Tài liệu này hướng dẫn chi tiết cách thiết lập môi trường phát triển cho dự án từ con số 0. Vui lòng thực hiện tuần tự các bước dưới đây.

---

## 1. Cài đặt Công cụ (Prerequisites)

Trước khi tải code, hãy đảm bảo máy tính của bạn đã cài đặt các công cụ sau.

### 1.1 SQL Server & ODBC Driver

Để chạy Database, bạn cần SQL Server và Driver để Python có thể kết nối.

1.  **Cài đặt SQL Server:** Tải bản **Developer** hoặc **Express** (Miễn phí) từ Microsoft.
2.  **Cài đặt SSMS (SQL Server Management Studio):** Công cụ để quản lý giao diện database.
3.  **Cài đặt ODBC Driver (Bắt buộc):**
    - Tải [ODBC Driver 17 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server).
    - _Lưu ý:_ Nếu không cài đúng phiên bản này, Python sẽ báo lỗi kết nối.

### 1.2 Ngrok (Công cụ Tunneling)

Dùng để công khai localhost ra internet cho Vercel kết nối.

#### Cách 1: Cài qua Microsoft Store (Khuyên dùng)

1.  Mở **Microsoft Store** trên Windows.
2.  Tìm kiếm từ khóa **"ngrok"**.
3.  Nhấn **Get** hoặc **Install**.
4.  Sau khi xong, mở CMD hoặc PowerShell gõ `ngrok` để kiểm tra.

#### Cách 2: Cài thủ công (Zip)

1.  Tải file ZIP từ [ngrok.com](https://dashboard.ngrok.com/get-started/setup/windows).
2.  Giải nén vào một thư mục cố định (Ví dụ: `C:\ngrok`).
3.  **Thêm vào PATH:**
    - Gõ "Edit the system environment variables" vào thanh Start.
    - Chọn **Environment Variables**.
    - Ở mục **System variables**, tìm dòng `Path` -> Nhấn **Edit**.
    - Nhấn **New** -> Dán đường dẫn thư mục ngrok vào (VD: `C:\ngrok`).
    - Nhấn OK liên tục để lưu.

#### Xác thực (Authentication)

1.  Đăng ký/Đăng nhập tại [Ngrok Dashboard](https://dashboard.ngrok.com/get-started/your-authtoken).
2.  Copy **Authtoken** của bạn.
3.  Mở Terminal và chạy lệnh:
    ```bash
    ngrok config add-authtoken <YOUR_TOKEN_HERE>
    ```

---

## 2. Thiết lập Database (SQL Server & Alembic)

### Bước 1: Tạo Database rỗng

1.  Mở **SSMS (SQL Server Management Studio)**.
2.  Kết nối vào Server của bạn (thường là `localhost` hoặc `.`).

### Bước 2: Cấu hình biến môi trường

1.  Vào thư mục gốc của dự án, tạo file `.env`.
2.  Thay đổi `DB_USER` và `DB_PASSWORD` thành SQL của bạn:
    ```bash
    DB_USER="trantien"
    DB_PASSWORD="12345678"
    ```

### Bước 3: Đồng bộ Database (Apply Migrations)

Vì dự án đã có sẵn folder `migrations/versions`, bạn **KHÔNG** chạy lệnh tạo mới. Hãy chạy lệnh sau để đồng bộ cấu trúc bảng vào database vừa tạo:

1.  Mở Terminal tại thư mục gốc dự án.
2.  Chạy lệnh:
    ```bash
    alembic upgrade head
    ```
    _(Lệnh này sẽ tạo toàn bộ bảng, cột và quan hệ đúng theo code hiện tại)_.

> **⚠️ Lưu ý cho Dev:** Nếu sau này bạn sửa đổi Models trong Python, hãy làm theo quy trình:
>
> 1. Sửa file model trong `backend/database/models/`.
> 2. Tạo file migration mới: `alembic revision --autogenerate -m "mô tả thay đổi"`
> 3. Cập nhật DB: `alembic upgrade head`

---

## 3. Chạy Dự án (Backend Local)

### Bước 1: Cài đặt thư viện Python

1.  Tạo môi trường ảo (Khuyên dùng):
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```
2.  Cài đặt các gói cần thiết:
    ```bash
    pip install -r requirements.txt
    ```

### Bước 2: Khởi động Backend

Mở một cửa sổ Terminal, chạy lệnh:

```bash
uvicorn backend.main:app
```

Sau đó mở thêm cửa sổ Terminal, chạy lệnh:

```bash
ngrok http <APP_PORT>
```

## 4. Triển khai Vercel (Initial Setup)

Phần này hướng dẫn đưa code lên Vercel lần đầu tiên.

### Bước 1: Push code lên GitHub

Đảm bảo code của bạn đã được đẩy lên một Repository trên GitHub.

### Bước 2: Import vào Vercel

1.  Truy cập [Vercel Dashboard](https://vercel.com/dashboard).
2.  Bấm **Add New...** -> **Project**.
3.  Ở mục **Import Git Repository**, chọn Repo GitHub của bạn.

### Bước 3: Cấu hình Project (Quan trọng)

Trong màn hình "Configure Project", hãy thiết lập chính xác như sau để tránh lỗi build Python:

1.  **Framework Preset:** Chọn **Other**.
2.  **Root Directory:** Để mặc định (`./`).
3.  **Build Command:** Bật **Override** và điền lệnh: `exit 0`
    _(Lệnh này báo Vercel bỏ qua bước build, chỉ serve file tĩnh và serverless function)_.
4.  **Output Directory:** Để trống (Empty).

### Bước 4: Thêm Biến Môi trường (Environment Variables)

Mở mục **Environment Variables** ngay trong màn hình cấu hình đó:

1.  **Key:** `BACKEND_URL`
2.  **Value:** Dán URL ngrok bạn vừa copy (VD: `https://a1b2-c3d4.ngrok-free.app`).
    - _Lưu ý: Không có dấu `/` ở cuối URL._
3.  Bấm **Add**.

### Bước 5: Deploy

Bấm nút **Deploy**. Vercel sẽ bắt đầu quá trình deploy và cung cấp cho bạn một đường link (VD: `https://hyper-data-lab.vercel.app`).

---

## 5. Quy trình Cập nhật Ngrok (Hằng ngày)

Mỗi khi bạn tắt máy hoặc tắt Ngrok, URL sẽ thay đổi. Frontend trên Vercel sẽ bị mất kết nối. Bạn cần làm các bước sau để cập nhật lại:

1.  **Chạy lại Ngrok:** Lấy URL HTTPS mới.
2.  **Vào Vercel Dashboard:** Chọn Project -> **Settings** -> **Environment Variables**.
3.  **Sửa `BACKEND_URL`:** Bấm icon cây bút chì, dán URL mới vào -> **Save**.
4.  **Redeploy (BẮT BUỘC):**
    - Vào tab **Deployments**.
    - Tại dòng trên cùng (Latest), bấm dấu **3 chấm (...)**.
    - Chọn **Redeploy**.
    - Đợi khoảng 30s-1p để hệ thống cập nhật biến môi trường mới.

---

## 6. Kiểm tra (Verify)

1.  Truy cập trang web trên Vercel sau khi redeploy xong.
2.  Nhấn **F12** -> Tab **Network**.
3.  Thực hiện một chức năng (Ví dụ: Bấm nút "Scrape").
4.  Kiểm tra request gửi đi. Nếu thấy trạng thái **200 OK** và data trả về, hệ thống đã kết nối thành công!
