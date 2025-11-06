import express from 'express'
import { saveSensorData } from '../controllers/sensor.controller';

export const sensorRouter = express.Router()
/**
 * @route   POST /api/sensor
 * @desc    Lưu dữ liệu cảm biến từ ESP32
 * @access  Public
 */
sensorRouter.post('/sensor', saveSensorData);