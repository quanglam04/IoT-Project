import mongoose from 'mongoose'
const { Schema } = mongoose

export enum AuditEvent {
  USER_LOGIN = 'Người dùng đã đăng nhập vào hệ thống',
  GET_USER_LIST = 'Lấy danh sách người dùng',
  GET_DEVICE_COUNT = 'Đếm số lượng thiết bị kết nối',
  GET_ESP32_REPORT = 'Xuất báo cáo dữ liệu từ ESP32',
  MANUAL_PUMP_CONTROL = 'Điều khiển bơm thủ công',
  UPDATE_FIRMWARE = 'Cập nhật firmware cho cảm biến',
  GET_AI_REPORT = 'Xuất báo cáo của AI',
}

const AuditSchema = new Schema(
  {
    actor: {
      type: String,
      required: [true, 'Tác nhân là bắt buộc'],
      trim: true
    },
    event: {
      type: String,
      required: [true, 'Sự kiện là bắt buộc'],
      trim: true,
      enum: Object.values(AuditEvent)
    },
    details: {
      type: String,
      required: true,
      trim: true
    }, 
    createdAt:{
        type: Date,
        default: Date.now
    }
  },
)

// đánh index để sắp xếp
AuditSchema.index({ createdAt: -1 })

const Audit = mongoose.model('Audit', AuditSchema)
export default Audit
