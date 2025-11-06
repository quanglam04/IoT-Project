export const HTTPStatus = {
  // --- 2xx Success ---
  OK: 200, // Yêu cầu thành công.
  CREATED: 201, // Yêu cầu đã thành công và tài nguyên mới đã được tạo. (Ví dụ: Đăng ký thành công)
  ACCEPTED: 202, // Yêu cầu đã được chấp nhận xử lý, nhưng quá trình xử lý chưa hoàn thành.
  NO_CONTENT: 204, // Yêu cầu thành công, nhưng không có nội dung để trả về. (Ví dụ: Xóa thành công)

  // --- 3xx Redirection ---
  MOVED_PERMANENTLY: 301, // Tài nguyên đã được chuyển đến một URL mới vĩnh viễn.
  SEE_OTHER: 303, // Xem tài nguyên tại URI khác (dùng cho POST redirect GET).
  NOT_MODIFIED: 304, // Tài nguyên chưa được sửa đổi kể từ yêu cầu cuối cùng.

  // --- 4xx Client Error ---
  BAD_REQUEST: 400, // Cú pháp yêu cầu không hợp lệ hoặc thiếu tham số/dữ liệu cần thiết.
  UNAUTHORIZED: 401, // Yêu cầu cần xác thực (Token bị thiếu hoặc không hợp lệ).
  FORBIDDEN: 403, // Máy chủ hiểu yêu cầu nhưng từ chối thực hiện (Ví dụ: Không có quyền truy cập).
  NOT_FOUND: 404, // Không tìm thấy tài nguyên được yêu cầu.
  METHOD_NOT_ALLOWED: 405, // Phương thức HTTP được sử dụng không được phép cho tài nguyên này.
  CONFLICT: 409, // Yêu cầu xung đột với trạng thái hiện tại của máy chủ (Ví dụ: Tài nguyên đã tồn tại).
  UNPROCESSABLE_ENTITY: 422, // Yêu cầu hợp lệ, nhưng không thể xử lý do lỗi ngữ nghĩa (Ví dụ: Lỗi validation chi tiết).
  TOO_MANY_REQUESTS: 429, // Người dùng đã gửi quá nhiều yêu cầu trong một khoảng thời gian nhất định (Rate limiting).

  // --- 5xx Server Error ---
  INTERNAL_SERVER_ERROR: 500, // Lỗi chung của máy chủ.
  NOT_IMPLEMENTED: 501, // Máy chủ không hỗ trợ chức năng cần thiết để thực hiện yêu cầu.
  BAD_GATEWAY: 502, // Máy chủ nhận được phản hồi không hợp lệ từ máy chủ ngược dòng.
  SERVICE_UNAVAILABLE: 503, // Máy chủ hiện không sẵn sàng (quá tải hoặc bảo trì).
  GATEWAY_TIMEOUT: 504 // Máy chủ không nhận được phản hồi kịp thời từ máy chủ ngược dòng.
}

export default HTTPStatus
