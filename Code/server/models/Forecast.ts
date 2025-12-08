import mongoose from 'mongoose'
import { Schema } from 'mongoose'

const ForecastSchema = new Schema({
    date: { 
        type: Date,
        required: true
    },
    chanceOfRain: { 
        type: Number,
        min: 0,
        max: 1
    },
    reason: { 
        type: String
    },
    shouldIrrigate: {
        type: Boolean
    },
    slot_time:{
        type: Date,
        required: true,
    }
});

const Forecast = mongoose.model('Forecast', ForecastSchema)
export default Forecast