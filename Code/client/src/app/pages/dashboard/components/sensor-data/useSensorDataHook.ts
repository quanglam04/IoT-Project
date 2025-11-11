import socketService from '@/services/socket.service'
import type { DataSensor } from '@/shared/types/sensor.type'
import { useEffect, useState } from 'react'

const useSensorDataHook = () => {
  const [sensorData, setSensorData] = useState<DataSensor>()
  socketService.connect()
  useEffect(() => {
    socketService.onReceiveDataFromSensor((data) => {
      console.log(`Data Sensor:`, data)
      setSensorData(data)
    })
  }, [sensorData, setSensorData])
  return { sensorData }
}
export default useSensorDataHook
