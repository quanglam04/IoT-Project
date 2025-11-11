import mqttClient from '../config/mqtt.config';
import logger from '../utils/log';
import { handleSensorData } from '../controllers/sensor.mqtt.controller';
import { handleDeviceStatus } from '../services/device.service';
import Topic from '../shared/constants/topic';

export const startMqttSubscriptions = () => {
  mqttClient.on('connect', () => {
    const topicsToSubscribe = [
      'sensor/data/push', 
      'devices/status/+'    
    ];
    
    mqttClient.subscribe(topicsToSubscribe, (err) => {
      if (!err) {
        logger.info(`Đã subscribe thành công các topic: ${topicsToSubscribe.join(', ')}`);
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
    if (topic === Topic.SENSOR_DATA_PUSH) {
      handleSensorData(payload);
    } 

    // topic status
    else if (topic.startsWith('devices/status/')) {
      handleDeviceStatus(topic, payload);
    } 

    else {
      logger.warn(`Không có trình xử lý (handler) cho topic: ${topic}`);
    }
  });
};