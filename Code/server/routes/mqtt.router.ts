import mqttClient from '../config/mqtt.config';
import logger from '../utils/log';
import { handleSensorData } from '../controllers/sensor.controller';
import { handleDeviceStatus } from '../services/device.service';
import Topic from '../shared/constants/topic';
import { handleIrrigationSchedule, handleRainForecast } from '../controllers/ai.controller';

let lastDeviceStatusReceivedAt: number = Date.now();
let check = true

// Hàm kiểm tra mỗi 5 giây, nếu 0 nhận được thì gửi emit là offline
const startDeviceStatusWatcher = () => {
  setInterval(() => {
    const now = Date.now();
    const diff = now - lastDeviceStatusReceivedAt;

    if (diff > 6000) { // > 6s để tránh nhiễu do lệch vài ms
      if (check) handleDeviceStatus('device/status/esp32-001', JSON.stringify({status: "offline"}));
      check = false
      if (check) logger.warn(`Không nhận được tin từ device/status/# nào trong ${Math.round(diff/1000)} giây`);

    }
  }, 5000); // chính xác mỗi 5 giây
};

export const startMqttSubscriptions = () => {
  mqttClient.on('connect', () => {
    const topicsToSubscribe = [
      'sensor/data/push', 
      'device/status/#',
      Topic.AI_FORECAST_RAIN,
      Topic.AI_SCHEDULE_IRRIGATION,  
    ];
    
    mqttClient.subscribe(topicsToSubscribe, (err) => {
      if (!err) {
        logger.info(`Đã subscribe thành công các topic: ${topicsToSubscribe.join(', ')}`);
        startDeviceStatusWatcher();
      } else {
        logger.error('MQTT subscribe lỗi:', err);
      }
    });
  });

  // khi có dữ liệu đến
  mqttClient.on('message', (topic, message) => {
    const payload = message.toString();

    //controller tương ứng
    if (topic === Topic.SENSOR_DATA_PUSH) {
      handleSensorData(payload);
    } 

    // topic device_status
    else if (topic.startsWith('device/status/')) {
      lastDeviceStatusReceivedAt = Date.now();
      handleDeviceStatus(topic, payload);
      check = true
    }

    else if (topic === Topic.AI_FORECAST_RAIN) {
      handleRainForecast(payload);
    }

    else if (topic === Topic.AI_SCHEDULE_IRRIGATION) {
      handleIrrigationSchedule(payload);
    }

    else {
      logger.warn(`Không có trình xử lý (handler) cho topic: ${topic}`);
    }
  });
};