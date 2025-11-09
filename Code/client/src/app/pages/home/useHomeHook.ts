import socketService from '@/services/socket.service'
import useNotificationHook from '@/shared/hook/useNotificationHook'
import type { DataSensor } from '@/shared/types/sensor.type'
import { useEffect, useState } from 'react'

const useHomeHook = () => {
  const [dataSensor, setDataSensor] = useState<DataSensor>({
    temperature: 0,
    humidity: 0,
    light: 0,
    soilMoisture: 0,
    timestamp: ''
  })
  const { showSuccess } = useNotificationHook()
  useEffect(() => {
    socketService.connect()
    socketService.onReceiveDataFromSensor((data) => {
      setDataSensor(data)
      showSuccess('Received data from sensor')
    })
    console.log(dataSensor)
  }, [dataSensor, showSuccess])
  return { dataSensor }
}
export default useHomeHook
