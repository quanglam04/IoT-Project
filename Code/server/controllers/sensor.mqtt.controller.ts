import logger from '../utils/log';
import SensorData from '../models/SensorData';
import mqttClient from '../config/mqtt.config';
import { Server } from 'socket.io';
import { io } from '..';

/**
 * Hàm làm tròn số 2 số sau thập phân
 */
const roundToTwo = (num: number): number => {
  if (typeof num !== 'number') return num;
  return parseFloat(num.toFixed(2));
};

/**
 * Hàm chuẩn hóa Date thành "dd/MM/yyyy"
 */
const formatDate = (date: string): string => {

  const newdate = new Date(date);

  const day = newdate.getDate().toString().padStart(2, '0');

  const month = (newdate.getMonth() + 1).toString().padStart(2, '0'); // getMonth() bắt đầu từ 0

  const year = newdate.getFullYear();

  return `${day}/${month}/${year}`;
};

/**
 * Xử lý tin nhắn từ topic 'sensor/data/push'
 */
export const handleSensorData = async (payload: string) => {
  try {
    const data = JSON.parse(payload);
    
    // 1. LƯU VÀO MONGODB
    const newData = new SensorData({
      temperature: roundToTwo(data.temperature),
      humidity: roundToTwo(data.humidity),
      light: roundToTwo(data.light),
      soilMoisture: roundToTwo(data.soilMoisture),
      timestamp: formatDate(data.timestamp)
    });

    const savedData = await newData.save();
    logger.info(`Đã lưu sensor data (MQTT): ${savedData._id}`);

    const emitData = {
      temperature: roundToTwo(data.temperature),
      humidity: roundToTwo(data.humidity),
      light: roundToTwo(data.light),
      soilMoisture: roundToTwo(data.soilMoisture),
      timestamp: formatDate(data.timestamp)
    };


    if(io){
      io.emit('sensor/data/push', emitData)
      logger.info(`Đã emit "sensor/data/push" tới client`);
      logger.info(JSON.stringify(emitData));
    }

  } catch (error) {
    logger.error(`Lỗi xử lý tin nhắn 'sensor/data/push': ${error}`);
  }
};