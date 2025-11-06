import mongoose from 'mongoose'
import { Schema } from 'mongoose'

const ScheduleSchema= new Schema(
    {
        action: {
            type: String,
            enum: ['ON', 'OFF'],
            default: 'OFF',
            required: true
        },
        duration: {
            type: Number,
            required: true,
            default: 300
        },
        startTime: {
            type: Date,
            default: Date.now,
            required: true
        },
        // nghĩ là nên thêm trường nữa để phân biệt giữa lịch AI hay lịch thủ công
        isManual: {
            type: Boolean,
            default: false
        }
    }
)

const Schedule = mongoose.model('Schedule', ScheduleSchema)
export default Schedule