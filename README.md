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
|   +-- alembic/
|   +-- .env.example
|   +-- alembic.ini
|   +-- pytest.ini
|   +-- requirements.txt
|   +-- seed.py
|
+-- frontend/
    +-- src/
    |   +-- api/
    |   +-- components/
    |   +-- hooks/
    |   +-- pages/
    |   +-- utils/
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
alembic upgrade head
python seed.py
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Nếu chỉ chạy demo nhanh bằng SQLite local, backend vẫn tự tạo bảng khi khởi động. Trong `ENVIRONMENT=production`, backend không tự tạo bảng; cần chạy `alembic upgrade head` trước khi start app. Cách khuyến nghị là chạy `alembic upgrade head`, sau đó chạy `python seed.py` để có tài khoản demo.

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

Frontend hiện đã tách theo module:

- `src/api/`: API client và xử lý lỗi phiên đăng nhập.
- `src/hooks/`: hook routing nội bộ.
- `src/components/`: component dùng chung như layout, notification, bảng, trạng thái loading/error.
- `src/pages/`: các trang theo role `student`, `company`, `admin`.
- `src/utils/`: helper chuyển đổi dữ liệu form.

Các URL chính của frontend:

```text
/student/home
/student/jobs
/student/companies
/student/applications
/student/profile
/student/forum
/student/forum/:id
/company/home
/company/jobs
/company/applicants
/company/profile
/admin/home
/admin/users
/admin/posts
/admin/job-positions
/admin/forum
/admin/skills
```

## Tài khoản đăng nhập và seed dữ liệu

Admin không được đăng ký công khai từ màn hình đăng ký. Khi chạy demo lần đầu, hãy seed tài khoản mẫu:

```powershell
cd backend
python seed.py
```

Script seed tạo các tài khoản:

```text
student@example.com / Password123!
company@example.com / Password123!
admin@example.com / Password123!
```

Sau khi có admin, admin có thể tạo thêm tài khoản qua API quản trị. Màn hình đăng ký công khai chỉ cho phép tạo `student` hoặc `company`.

## Luồng demo đề xuất

1. Đăng ký tài khoản `company`.
2. Đăng nhập bằng tài khoản company.
3. Tạo hồ sơ công ty.
4. Đăng một vị trí thực tập.
5. Đăng nhập tài khoản `admin` đã seed.
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

Dự án đã có Alembic migrations để quản lý thay đổi schema. Sau khi cài dependencies, có thể chạy:

```powershell
cd backend
alembic upgrade head
```

Khi cần tạo migration mới sau khi sửa model:

```powershell
cd backend
alembic revision --autogenerate -m "describe change"
```

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
- `job_positions`: danh mục vị trí tuyển dụng chuẩn hóa
- `applications`: hồ sơ ứng tuyển
- `skills`: danh sách kỹ năng dùng để lọc và nhập liệu
- `notifications`: thông báo trong hệ thống

Quan hệ chính:

```text
users 1 - 1 student_profiles
users 1 - 1 companies
companies 1 - n internship_posts
job_positions 1 - n internship_posts
student_profiles 1 - n applications
internship_posts 1 - n applications
```

CV không lưu trực tiếp trong database. File CV được lưu trên S3 private bucket, database chỉ lưu object key hoặc storage reference. Khi cần xem CV, backend tạo presigned URL tạm thời cho user có quyền truy cập.

## Module phân tích yêu cầu tuyển dụng

Hệ thống đã chuẩn hóa thêm dữ liệu bài đăng để phân tích thị trường tuyển dụng:

- `position_id`: vị trí tuyển dụng chọn từ bảng `job_positions`
- `required_skills`: kỹ năng yêu cầu, nhập dạng danh sách phân tách bằng dấu phẩy
- `experience_level`: Intern, Fresher, Junior, Middle, Senior
- `job_type`: Internship, Full-time, Part-time, Contract, Freelance
- `salary_min`, `salary_max`: khoảng lương
- `education_requirement`: yêu cầu học vấn
- `location`: địa điểm tuyển dụng

Frontend sinh viên có trang `Career Market Insights` tại:

```text
/student/insights
```

Trang này hiển thị kỹ năng được yêu cầu nhiều, vị trí tuyển nhiều, yêu cầu kinh nghiệm, xu hướng lương và địa điểm tuyển dụng.

Admin quản lý danh sách vị trí chuẩn tại:

```text
/admin/job-positions
```

Admin có thể thêm, sửa, ẩn/hiện và xóa vị trí tuyển dụng. Mỗi vị trí có thể gán ngành nghề và danh sách kỹ năng gợi ý. Khi công ty đăng tuyển, công ty phải chọn vị trí từ danh sách đang active; các kỹ năng gợi ý sẽ hiện thành chip để tick chọn.

## Module diễn đàn cộng đồng chuyên môn

Hệ thống có các cộng đồng theo chuyên môn như Information Technology, Marketing, Logistics, Business, Food & Beverage, Hospitality và Part-time Jobs.

Ứng viên có thể:

- Đăng bài viết hoặc đặt câu hỏi
- Chọn loại bài: Question, Academic Post, Experience Sharing, Resource, Discussion
- Bình luận vào bài viết
- Like bài viết
- Lưu bài viết
- Chia sẻ liên kết bài viết

Bài `Academic Post` và `Resource` mặc định ở trạng thái `Pending` để admin duyệt trước. Các loại bài khác được hiển thị ngay ở cộng đồng.

Admin quản trị diễn đàn tại:

```text
/admin/forum
```

Admin có thể thêm/ẩn community category, duyệt bài, ẩn bài, từ chối bài, xóa bài không phù hợp và khóa người dùng spam qua màn hình quản lý người dùng.

## API chính

Auth:
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

Common:
- `GET /skills`
- `GET /job-positions`
- `GET /companies`
- `GET /notifications`
- `PATCH /notifications/{id}/read`
- `GET /students/dashboard`
- `GET /company/dashboard`

Forum:
- `GET /forum/categories`
- `GET /forum/posts`
- `POST /forum/posts`
- `GET /forum/posts/{id}`
- `GET /forum/posts/{id}/comments`
- `POST /forum/posts/{id}/comments`
- `POST /forum/posts/{id}/like`
- `POST /forum/posts/{id}/save`

Student:
- `GET /internships`
- `GET /internships/{id}`
- `GET /students/profile`
- `POST /students/profile`
- `PATCH /students/profile`
- `POST /students/upload-cv`
- `POST /applications`
- `GET /applications/me`

Company:
- `GET /company/profile`
- `POST /company/profile`
- `PATCH /company/profile`
- `POST /company/internships`
- `GET /company/internships`
- `GET /company/applications`
- `GET /company/applications/{id}/cv` - tạo presigned URL tạm thời để xem CV ứng viên
- `PATCH /company/applications/{id}/status`

Analytics:
- `GET /analytics/top-skills`
- `GET /analytics/top-positions`
- `GET /analytics/top-locations`
- `GET /analytics/salary-summary`
- `GET /analytics/skill-by-position/{position_id}`
- `GET /analytics/job-market-summary`

Admin:
- `GET /admin/users`
- `POST /admin/users`
- `PATCH /admin/users/{id}/status`
- `GET /admin/dashboard`
- `POST /admin/skills`
- `GET /admin/job-positions`
- `POST /admin/job-positions`
- `PATCH /admin/job-positions/{id}`
- `DELETE /admin/job-positions/{id}`
- `GET /admin/forum/categories`
- `POST /admin/forum/categories`
- `PATCH /admin/forum/categories/{id}`
- `DELETE /admin/forum/categories/{id}`
- `GET /admin/forum/posts`
- `PATCH /admin/forum/posts/{id}/status`
- `DELETE /admin/forum/posts/{id}`
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

Kiểm tra frontend production build:

```powershell
cd frontend
npm.cmd run build
```

Lưu ý: script build dùng `vite build .` để build ổn định trên Windows khi đường dẫn thư mục có dấu tiếng Việt.

Test hiện tại kiểm tra luồng chính:

- Company tạo bài đăng
- Admin duyệt bài
- Student upload CV và apply
- Company cập nhật trạng thái ứng tuyển
- Company xem CV ứng viên qua presigned URL
- Notification được tạo khi trạng thái thay đổi
- Duplicate apply, deadline hết hạn, tài khoản bị khóa và phân quyền bị chặn đúng
- Validation cho GPA, số lượng tuyển và kích thước file CV
- Analytics thị trường tuyển dụng, top skills, top positions và skill theo từng job position
- Forum community: đăng bài, bài cần duyệt, comment, like, save và admin moderation
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
S3_PRESIGNED_URL_EXPIRE_SECONDS=300
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

CORS và cookie khi deploy production:

```env
BACKEND_CORS_ORIGINS=https://your-frontend-domain.com
BACKEND_CORS_ORIGIN_REGEX=
REFRESH_COOKIE_SECURE=true
REFRESH_COOKIE_SAMESITE=none
```

Ở production, backend chỉ chấp nhận CORS origin dạng HTTPS cụ thể, không dùng wildcard và không dùng regex local/LAN. Nếu frontend và API dùng hai origin khác nhau, refresh cookie cần `SameSite=none` và `Secure=true`.

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
