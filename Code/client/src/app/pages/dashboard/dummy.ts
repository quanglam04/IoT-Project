const pumpStatus = {
  status: 'OFF',
  aiPrediction: {
    rainProbability: 82,
    suggestion: 'Hoãn tưới 90 phút'
  }
}

const devices = [
  { name: 'ESP32', status: 'online' },
  { name: 'Pump', status: 'online' }
]

const decisions = [
  {
    time: '08:00',
    p60m: '0.82',
    action: 'Hoãn tưới',
    note: 'Khả năng mưa thấp vẫn tưới'
  },
  {
    time: '10:00',
    p60m: '0.45',
    action: 'Tưới 10m',
    note: 'Soil 38%'
  }
]

const alerts = [
  {
    message: 'Đất khô: 38%',
    time: '10mm ago'
  },
  {
    message: 'Độ ẩm không khí cao',
    time: '2h ago'
  }
]

const sensorData = {
  lastUpdate: '00:00:00 AM',
  temperature: '29.0',
  humidity: '72',
  soilMoisture: '40',
  airPressure: '1013.2'
}

export { pumpStatus, devices, decisions, alerts, sensorData }
