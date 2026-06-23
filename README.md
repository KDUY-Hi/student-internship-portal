# Cloud-based Student Internship Portal on AWS

Đây là dự án web app quản lý và tìm kiếm thực tập cho sinh viên. Sinh viên có thể tạo hồ sơ, upload CV, tìm vị trí thực tập và nộp đơn. Doanh nghiệp có thể đăng bài tuyển thực tập, xem ứng viên và cập nhật trạng thái hồ sơ. Admin có thể quản lý người dùng và duyệt bài đăng thực tập.

Dự án được xây dựng theo hướng phù hợp với đề tài **Application Development on AWS**: có frontend, backend, database, lưu file, xác thực người dùng, logging cơ bản và có thể deploy lên AWS bằng EC2, S3, RDS và CloudWatch.

## Công nghệ sử dụng

- **Frontend:** ReactJS + Vite
- **Backend:** FastAPI
- **Database local:** SQLite
- **Database AWS:** PostgreSQL trên Amazon RDS
- **File storage:** Amazon S3 cho file CV
- **Authentication:** JWT
- **ORM:** SQLAlchemy
- **Validation:** Pydantic
- **Monitoring khi deploy:** CloudWatch Logs

## Chức năng chính

Sinh viên:
- Đăng ký, đăng nhập
- Tạo và cập nhật hồ sơ cá nhân
- Upload CV
- Xem và tìm kiếm vị trí thực tập
- Tìm kiếm công ty theo tên, mô tả hoặc địa điểm
- Nộp đơn ứng tuyển
- Xem trạng thái ứng tuyển
- Xem thống kê số đơn ứng tuyển
- Nhận thông báo khi trạng thái ứng tuyển thay đổi

Doanh nghiệp:
- Đăng ký, đăng nhập
- Tạo hồ sơ công ty
- Đăng vị trí thực tập
- Xem danh sách ứng viên
- Cập nhật trạng thái ứng tuyển: `Pending`, `Reviewed`, `Interview`, `Accepted`, `Rejected`
- Xem thống kê số bài đăng và số ứng viên
- Nhận thông báo khi admin duyệt hoặc từ chối bài đăng

Admin:
- Xem danh sách người dùng
- Khóa hoặc mở khóa tài khoản người dùng
- Xem các bài đăng đang chờ duyệt
- Duyệt, từ chối hoặc đóng bài đăng thực tập
- Xóa bài đăng không phù hợp
- Quản lý danh sách kỹ năng
- Xem dashboard thống kê tổng quan

## Cấu trúc thư mục

```text
.
+-- backend/
|   +-- app/
|   |   +-- routers/
|   |   +-- auth.py
|   |   +-- config.py
|   |   +-- database.py
|   |   +-- main.py
|   |   +-- models.py
|   |   +-- schemas.py
|   |   +-- services.py
|   +-- tests/
|   +-- .env.example
|   +-- pytest.ini
|   +-- requirements.txt
|
+-- frontend/
    +-- src/
    |   +-- main.jsx
    |   +-- styles.css
    +-- .env.example
    +-- index.html
    +-- package.json
```

## Cách chạy backend

Mở terminal tại thư mục gốc dự án, sau đó chạy:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend chạy tại:

```text
http://localhost:8000
```

Kiểm tra backend:

```text
http://localhost:8000/health
```

Swagger API docs:

```text
http://localhost:8000/docs
```

## Cách chạy frontend

Mở terminal thứ hai tại thư mục gốc dự án, sau đó chạy:

```powershell
cd frontend
npm.cmd install
Copy-Item .env.example .env
npm.cmd run dev -- --host 0.0.0.0
```

Frontend chạy tại:

```text
http://localhost:5173
```

Nếu mở bằng IP LAN, ví dụ:

```text
http://10.215.198.254:5173
```

thì backend cũng cần đang chạy ở:

```text
http://10.215.198.254:8000
```

Frontend mặc định sẽ tự gọi backend theo cùng hostname và port `8000`. Khi deploy thật, có thể cấu hình `VITE_API_URL` trong `frontend/.env`.

## Tài khoản đăng nhập

Dự án chưa seed sẵn tài khoản. Khi chạy lần đầu, hãy dùng màn hình **Create account** để tạo 3 loại tài khoản:

- Student: chọn role `student`
- Company: chọn role `company`
- Admin: chọn role `admin`

Ví dụ có thể tạo:

```text
student@example.com / 123456
company@example.com / 123456
admin@example.com / 123456
```

## Luồng demo đề xuất

1. Đăng ký tài khoản `company`.
2. Đăng nhập bằng tài khoản company.
3. Tạo hồ sơ công ty.
4. Đăng một vị trí thực tập.
5. Đăng ký hoặc đăng nhập tài khoản `admin`.
6. Admin duyệt bài đăng thực tập.
7. Đăng ký hoặc đăng nhập tài khoản `student`.
8. Student tạo hồ sơ, upload CV.
9. Student xem danh sách internship và apply.
10. Company xem danh sách ứng viên và cập nhật trạng thái hồ sơ.

Lưu ý: sinh viên chỉ thấy các bài internship đã được admin duyệt.

## Database

Local mặc định dùng SQLite:

```env
DATABASE_URL=sqlite:///./internship_portal.db
```

Khi chạy backend, database local sẽ được tạo tự động.

Nếu bạn đã chạy phiên bản cũ của dự án trước khi schema được bổ sung, hãy xóa file SQLite cũ rồi chạy lại backend:

```powershell
Remove-Item backend\internship_portal.db
```

Lệnh này chỉ cần dùng cho môi trường local SQLite. Khi xóa file này, dữ liệu demo cũ cũng sẽ mất.

Các bảng chính:

- `users`: tài khoản đăng nhập của student, company, admin
- `student_profiles`: hồ sơ sinh viên
- `companies`: hồ sơ doanh nghiệp
- `internship_posts`: bài đăng thực tập
- `applications`: hồ sơ ứng tuyển
- `skills`: danh sách kỹ năng dùng để lọc và nhập liệu
- `notifications`: thông báo trong hệ thống

Quan hệ chính:

```text
users 1 - 1 student_profiles
users 1 - 1 companies
companies 1 - n internship_posts
student_profiles 1 - n applications
internship_posts 1 - n applications
```

CV không lưu trực tiếp trong database. File CV được lưu trên S3, database chỉ lưu URL hoặc key của file.

## API chính

Auth:
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

Common:
- `GET /skills`
- `GET /companies`
- `GET /notifications`
- `PATCH /notifications/{id}/read`
- `GET /students/dashboard`
- `GET /company/dashboard`

Student:
- `GET /internships`
- `GET /internships/{id}`
- `POST /students/profile`
- `PATCH /students/profile`
- `POST /students/upload-cv`
- `POST /applications`
- `GET /applications/me`

Company:
- `POST /company/profile`
- `PATCH /company/profile`
- `POST /company/internships`
- `GET /company/internships`
- `GET /company/applications`
- `GET /company/applications/{id}/cv`
- `PATCH /company/applications/{id}/status`

Admin:
- `GET /admin/users`
- `PATCH /admin/users/{id}/status`
- `GET /admin/dashboard`
- `POST /admin/skills`
- `GET /admin/internships`
- `GET /admin/internships/pending`
- `PATCH /admin/internships/{id}/approve`
- `PATCH /admin/internships/{id}/status`
- `DELETE /admin/internships/{id}`

## Chạy test

```powershell
cd backend
python -m pytest
```

Test hiện tại kiểm tra luồng chính:

- Company tạo bài đăng
- Admin duyệt bài
- Student upload CV và apply
- Company cập nhật trạng thái ứng tuyển
- Company xem link CV của ứng viên
- Notification được tạo khi trạng thái thay đổi
- Admin dashboard và skills hoạt động
- API admin bị chặn nếu user không có quyền admin

## Ghi chú deploy AWS

Backend trên EC2:
- Cài Python và dependencies.
- Copy thư mục `backend/` lên EC2.
- Chạy FastAPI bằng Uvicorn:

```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Database trên RDS PostgreSQL:

```env
DATABASE_URL=postgresql+psycopg2://db_user:db_password@your-rds-endpoint:5432/internship_portal
```

CV trên S3:

```env
AWS_REGION=ap-southeast-1
S3_BUCKET_NAME=your-cv-bucket
S3_PUBLIC_BASE_URL=https://your-cv-bucket.s3.ap-southeast-1.amazonaws.com
```

Frontend trên S3 Static Website Hosting:

```powershell
cd frontend
npm.cmd run build
aws s3 sync dist/ s3://your-frontend-bucket --delete
```

CloudWatch:
- Cài CloudWatch Agent trên EC2.
- Đẩy log backend stdout/stderr lên CloudWatch Logs.

## Troubleshooting

Nếu frontend báo không kết nối được backend API:

1. Kiểm tra backend đã chạy chưa:

```text
http://localhost:8000/health
```

2. Nếu mở frontend bằng IP LAN, kiểm tra backend bằng IP đó:

```text
http://<your-ip>:8000/health
```

3. Chạy backend với `--host 0.0.0.0` để máy khác hoặc browser qua IP LAN truy cập được.

4. Nếu dùng PowerShell trên Windows và `npm` bị chặn, dùng `npm.cmd` thay cho `npm`.
