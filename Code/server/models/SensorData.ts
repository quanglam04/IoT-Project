import mongoose from 'mongoose'
import { Schema } from 'mongoose'

const SensorDataSchema = new Schema(
    {
        temperature: {
            type: Number,
            required: true
        }, 
        humidity: {
            type: Number,
            required: true
        },
        light: {
            type: Number,
            required: true
        },
        soilMoisture: {
            type: Number,
            required: true
        },
        timestamp: {
            type: Date,
            default: Date.now,
            required: true
        }
    }
)

const SensorData = mongoose.model('SensorData', SensorDataSchema)
export default SensorData