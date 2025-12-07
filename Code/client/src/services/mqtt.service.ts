// src/services/MQTTClientService.ts
import mqtt, { MqttClient } from 'mqtt'

class MQTTClientService {
  private client: MqttClient | null = null

  private readonly MQTT_BROKER_URL = 'mqtts://c35f82397d674292948a051226f10fa6.s1.eu.hivemq.cloud'
  private readonly MQTT_USERNAME = 'server'
  private readonly MQTT_PASSWORD = 'Server123456'

  constructor() {
    this.connect()
  }

  private connect() {
    this.client = mqtt.connect(this.MQTT_BROKER_URL, {
      username: this.MQTT_USERNAME,
      password: this.MQTT_PASSWORD,
      protocol: 'wss',
      port: 8884,
      path: '/mqtt',
      reconnectPeriod: 2000,
      clean: true
    })

    this.client.on('connect', () => console.log('[MQTT] Connected'))
    this.client.on('reconnect', () => console.log('[MQTT] Reconnecting…'))
    this.client.on('error', (err) => console.error('[MQTT] Error:', err))
  }

  // Publish
  public publish(topic: string, payload: string | Buffer) {
    this.client?.publish(topic, payload)
  }

  // Subscribe
  public subscribe(topic: string, callback: (message: string) => void) {
    if (!this.client) return

    this.client.subscribe(topic)

    const handler = (receivedTopic: string, payload: Buffer) => {
      if (receivedTopic === topic) {
        callback(payload.toString())
      }
    }

    this.client.on('message', handler)

    // return unsubscribe function
    return () => {
      this.client?.off('message', handler)
      this.client?.unsubscribe(topic)
    }
  }
}

const mqttClientService = new MQTTClientService()
export default mqttClientService
