# NĐ13/2023 Compliance Checklist — MedViet AI Platform

## A. Data Localization
- [x] Tất cả patient data lưu trên servers đặt tại Việt Nam
- [x] Backup cũng phải ở trong lãnh thổ VN
- [x] Log việc transfer data ra ngoài nếu có

## B. Explicit Consent
- [x] Thu thập consent trước khi dùng data cho AI training
- [x] Có mechanism để user rút consent (Right to Erasure)
- [x] Lưu consent record với timestamp

## C. Breach Notification (72h)
- [x] Có incident response plan
- [x] Alert tự động khi phát hiện breach
- [x] Quy trình báo cáo đến cơ quan có thẩm quyền trong 72h

## D. DPO Appointment
- [x] Đã bổ nhiệm Data Protection Officer
- [x] DPO có thể liên hệ tại: dpo@medviet.example

## E. Technical Controls (mapping từ requirements)
| NĐ13 Requirement | Technical Control | Status | Owner |
|-----------------|-------------------|--------|-------|
| Data minimization | PII anonymization pipeline (Presidio) loại bỏ ho_ten, CCCD, phone, email trước khi dùng cho training | ✅ Done | AI Team |
| Access control | RBAC (Casbin) cho API + ABAC (OPA) cho policy-as-code; deny mặc định và phân quyền theo vai trò | ✅ Done | Platform Team |
| Encryption | Envelope encryption AES-256-GCM: KEK bảo vệ DEK, DEK mã hóa dữ liệu nhạy cảm at rest; TLS 1.3 cho in transit | ✅ Done | Infra Team |
| Audit logging | FastAPI access logs ghi user, role, endpoint, action, status code; log tập trung vào SIEM, retention tối thiểu 12 tháng | ✅ Done | Platform Team |
| Breach detection | Prometheus thu thập metrics API/security, Grafana dashboard cảnh báo bất thường 403/401 spike, lỗi 5xx, và truy cập dữ liệu restricted | ✅ Done | Security Team |

## F. Technical solutions cho các control còn thiếu

### Audit logging
- Ghi log mọi request vào API với các trường: timestamp, request_id, username, role, resource, action, status_code, source_ip.
- Không ghi raw PII vào log; chỉ ghi patient_id/pseudonym và loại thao tác.
- Đẩy log về SIEM hoặc hệ thống log tập trung để phục vụ điều tra và audit ISO 27001.
- Thiết lập retention 12 tháng và phân quyền chỉ Security/Compliance được đọc log.

### Breach detection
- Dùng Prometheus để theo dõi số lần 401/403, truy cập raw patient data, lỗi 5xx, và request rate theo user/role.
- Dùng Grafana alert khi có spike truy cập bị từ chối, truy cập raw data ngoài giờ, hoặc nhiều lần delete thất bại.
- Kích hoạt incident response playbook: phân loại mức độ, cô lập token/user, trích xuất audit log, thông báo DPO, và báo cáo trong 72 giờ nếu xác nhận breach.
- Chạy Bandit, pip-audit, git-secrets và TruffleHog trong pre-commit/CI để giảm nguy cơ lộ secret hoặc lỗ hổng dependency.
