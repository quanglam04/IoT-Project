import mongoose from 'mongoose'
import { Schema } from 'mongoose'

const ScheduleSchema= new Schema(
    {
        start: {
            type: Date,
            required: true
        },
        end: {
            type: Date,
            required: true
        },
        durationMin: {
            type: Number,
            required: true
        },
        date: {
            type: String,
            required: true
        },
        note: {
            type: String,
            required: true
        },
        decision: {
            type: Boolean,
            default: true,
        }
    }
)

const Schedule = mongoose.model('Schedule', ScheduleSchema)
export default Schedule