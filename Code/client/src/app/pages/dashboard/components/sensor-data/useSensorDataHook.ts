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

  useEffect(() => {
    const savedData = storageService.get('dataSensor') ? JSON.parse(storageService.get('dataSensor') as string) : ''
    setSensorData(savedData)
  }, [])
  return { sensorData }
}
export default useSensorDataHook
