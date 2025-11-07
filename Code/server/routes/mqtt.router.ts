import mqttClient from '../config/mqtt.config';
import logger from '../utils/log';
import { handleSensorData } from '../controllers/sensor.mqtt.controller';

export const startMqttSubscriptions = () => {
  mqttClient.on('connect', () => {
    const topicSensorPushData = 'sensor/data/push';
    
    mqttClient.subscribe(topicSensorPushData, (err) => {
      if (!err) {
        logger.info(`Đã subscribe thành công topic: ${topicSensorPushData}`);
      } else {
        logger.error('MQTT subscribe lỗi:', err);
      }
    });
  });

  // khi có dữ liệu đến
  mqttClient.on('message', (topic, message) => {
    logger.info(`Nhận được tin nhắn từ topic: ${topic}`);
    const payload = message.toString();

    //controller tương ứng
    switch (topic) {
      case 'sensor/data/push':
        handleSensorData(payload);
        break;
      
      default:
        logger.warn(`Không có trình xử lý (handler) cho topic: ${topic}`);
    }
  });
};