import mongoose from 'mongoose'
import { Schema } from 'mongoose'

const DecisionAISchema = new Schema({
    date: { 
        type: Date,
        required: true
    },
    reason: { 
        type: String
    },
    decision: {
        type: Boolean,
        default: true,
    }
});

const DecisionAI = mongoose.model('DecisionAI', DecisionAISchema)
export default DecisionAI