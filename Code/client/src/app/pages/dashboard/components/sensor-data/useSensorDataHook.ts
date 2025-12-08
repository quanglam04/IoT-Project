import socketService from '@/services/socket.service'
import storageService from '@/shared/services/storage.service'
import type { DataSensor } from '@/shared/types/sensor.type'
import { useEffect, useState } from 'react'

const useSensorDataHook = () => {
  const [sensorData, setSensorData] = useState<DataSensor>()
  socketService.connect()
  useEffect(() => {
    socketService.onReceiveDataFromSensor((data) => {
      setSensorData(data)
      storageService.set('dataSensor', JSON.stringify(data))
    })
  }, [sensorData, setSensorData])

  const getSoilMoistureStatus = (value: number) => {
    if (value < 30) return 'Rất khô'
    if (value < 50) return 'Khá khô'
    if (value < 60) return 'Hơi khô'
    if (value <= 80) return 'Đủ ẩm'
    return 'Quá ẩm'
  }

  const getHumidityStatus = (value: number) => {
    if (value < 40) return 'Quá khô'
    if (value < 60) return 'Lý tưởng'
    if (value < 70) return 'Hơi ẩm'
    return 'Quá cao'
  }

  const getTemperatureStatus = (value: number) => {
    if (value < 20) return 'Hơi lạnh'
    if (value < 25) return 'Mát mẻ'
    if (value < 30) return 'Dễ chịu'
    return 'Nóng'
  }

  const getPressureStatus = (value: number) => {
    if (value < 1000) return 'Thấp'
    if (value < 1013.25) return 'Hơi thấp'
    return 'Cao'
  }

  useEffect(() => {
    const savedData = storageService.get('dataSensor') ? JSON.parse(storageService.get('dataSensor') as string) : ''
    setSensorData(savedData)
  }, [])
  return { sensorData, getSoilMoistureStatus, getHumidityStatus, getTemperatureStatus, getPressureStatus }
}
export default useSensorDataHook
