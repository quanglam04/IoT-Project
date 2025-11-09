import logger from '../utils/log';
import SensorData from '../models/SensorData';
import mqttClient from '../config/mqtt.config';
import { Server } from 'socket.io';
import { io } from '..';

/**
 * Hàm làm tròn số 2 số sau thập phân
 * @params num
 * @return {số thập phân sau khi xử lý}
 */
const roundToTwo = (num: number): number => {
  if (typeof num !== 'number') return num;
  return parseFloat(num.toFixed(2));
};

/**
 * Hàm chuẩn hóa Date thành "dd/MM/yyyy"
 * @param date
 * @returns {định dạng ngày sau khi xử lý}
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
    
    // biến để gửi thẳng lên client qua socket
    const emitData = {
      temperature: roundToTwo(data.temperature),
      humidity: roundToTwo(data.humidity),
      light: roundToTwo(data.light),
      soilMoisture: roundToTwo(data.soilMoisture),
      timestamp: formatDate(data.timestamp)
    };

    // biến model để lưu vào db
    const newData = new SensorData(emitData)

    const savedData = await newData.save();
    logger.info(`Đã lưu sensor data (MQTT): ${savedData._id}`);

    // phát sự kiện tới client, bên client lắng nghe để lấy dữ liệu
    if(io){
      io.emit('sensor/data/push', emitData)
      logger.info(`Đã emit "sensor/data/push" tới client`);
      logger.info(JSON.stringify(emitData));
    }

  } catch (error) {
    logger.error(`Lỗi xử lý tin nhắn 'sensor/data/push': ${error}`);
  }
};