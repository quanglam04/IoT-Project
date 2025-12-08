interface DataSensor {
  temperature: number
  humidity: number
  soilMoisture: number
  pressureHpa: number
  timestamp: string
}

interface AIPrediction {
  chanceOfRain: number
  date: string
  recommendation: string
  shouldIrrigate: boolean
}

export type { DataSensor, AIPrediction }
