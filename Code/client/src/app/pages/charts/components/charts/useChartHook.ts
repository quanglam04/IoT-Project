import { useEffect, useState } from 'react'
import { humidityData, pressureData, temperatureData } from '../../dummy'
import clientService from '@/services/client.service'

export type DataType = {
  time: string
  value: number
}

const useChartHook = () => {
  const [temperatureArr, setTemperatureArr] = useState<DataType[]>([])
  const [pressureArr, setPressureArr] = useState<DataType[]>([])
  const [soilMoistureArr, setSoilMoistureArr] = useState<DataType[]>([])

  const fetchData = async () => {
    const response = await clientService.getDataSensor()
    if (response.status === 200) {
      const data = response.data.data
      const temperatureArrResponse = data.temperatureArr
      const pressureArrResponse = data.pressureArr
      const soilMoistureArrResponse = data.soilMoistureArr
      setTemperatureArr([...temperatureArrResponse])
      setPressureArr([...pressureArrResponse])
      setSoilMoistureArr([...soilMoistureArrResponse])
      console.log(temperatureArrResponse, pressureArrResponse, soilMoistureArrResponse)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  return { temperatureArr, pressureArr, soilMoistureArr }
}
export default useChartHook
