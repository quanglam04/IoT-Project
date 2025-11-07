import logger from '../utils/log';
import SensorData from '../models/SensorData';
import mqttClient from '../config/mqtt.config';

/**
 * Xử lý tin nhắn từ topic 'sensor/data/push'
 */
export const handleSensorData = async (payload: string) => {
  try {
    const data = JSON.parse(payload);

    // 1. LƯU VÀO MONGODB
    const newData = new SensorData({
      temperature: data.temperature,
      humidity: data.humidity,
      light: data.light,
      soilMoisture: data.soilMoisture,
      timestamp: data.timestamp || new Date()
    });
    
    const savedData = await newData.save();
    logger.info(`Đã lưu sensor data (MQTT): ${savedData._id}`);

  } catch (error) {
    logger.error(`Lỗi xử lý tin nhắn 'sensor/data/push': ${error}`);
  }
};