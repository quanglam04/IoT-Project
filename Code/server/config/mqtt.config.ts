// config/mqtt.config.ts
import mqtt from 'mqtt';
import logger from '../utils/log';

const MQTT_BROKER_URL = process.env.MQTT_BROKER_URL
const MQTT_USERNAME = process.env.MQTT_USERNAME;
const MQTT_PASSWORD = process.env.MQTT_PASSWORD;

const options: mqtt.IClientOptions = {
  username: MQTT_USERNAME,
  password: MQTT_PASSWORD,
};

const mqttClient = mqtt.connect(MQTT_BROKER_URL as string, options);

mqttClient.on('connect', () => {
  logger.info(`MQTT đã kết nối tới Broker: ${MQTT_BROKER_URL}`);
});

mqttClient.on('error', (err) => {
  logger.error('MQTT Lỗi kết nối:', err);
});

mqttClient.on('close', () => {
  logger.warn('MQTT đã ngắt kết nối');
});

export default mqttClient;