import type { DataType } from './components/charts/useChartHook'

const timeRanges = [
  { value: '3h', label: '3h' },
  { value: '24h', label: '24h' },
  { value: '3d', label: '3d' },
  { value: '7d', label: '7d' }
]
const temperatureData: DataType[] = [
  { time: '00:00', value: 22 },
  { time: '04:00', value: 20 },
  { time: '08:00', value: 24 },
  { time: '12:00', value: 28 },
  { time: '16:00', value: 30 },
  { time: '20:00', value: 26 },
  { time: '24:00', value: 23 }
]

const humidityData: DataType[] = [
  { time: '00:00', value: 65 },
  { time: '04:00', value: 70 },
  { time: '08:00', value: 68 },
  { time: '12:00', value: 55 },
  { time: '16:00', value: 50 },
  { time: '20:00', value: 58 },
  { time: '24:00', value: 62 }
]

const pressureData: DataType[] = [
  { time: '00:00', value: 1013 },
  { time: '04:00', value: 1015 },
  { time: '08:00', value: 1014 },
  { time: '12:00', value: 1012 },
  { time: '16:00', value: 1011 },
  { time: '20:00', value: 1013 },
  { time: '24:00', value: 1014 }
]

export { timeRanges, temperatureData, humidityData, pressureData }
