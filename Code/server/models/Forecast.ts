import mongoose from 'mongoose'
import { Schema } from 'mongoose'

const ForecastSchema = new Schema({
    date: { 
        type: Date,
        required: true
    },
    predictedTemperature: {
        type: Number
    },
    predictedHumidity: {
        type: Number
    },
    chanceOfRain: { 
        type: Number,
        min: 0,
        max: 100
    },
    recommendation: { 
        type: String
    }
}
);

// cái này chưa biết để nhiều dự báo hay bao nhiêu nên để mặc định 1 nhé
ForecastSchema.index({ date: 1 }, { unique: true });

const Schedule = mongoose.model('Forecast', ForecastSchema)
export default Schedule