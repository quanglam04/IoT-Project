import useNotificationHook from '@/shared/hook/useNotificationHook'
import { useState } from 'react'

const useConfigHook = () => {
  const { showSuccess } = useNotificationHook()
  const [soilMoistureThreshold, setSoilMoistureThreshold] = useState('40')
  const [rainProbabilityThreshold, setRainProbabilityThreshold] = useState('0.7')
  const handleSaveConfig = () => {
    console.log('Saving config:', {
      soilMoistureThreshold,
      rainProbabilityThreshold
    })
    showSuccess('Cấu hình đã được lưu!')
  }
  return {
    soilMoistureThreshold,
    rainProbabilityThreshold,
    handleSaveConfig,
    setSoilMoistureThreshold,
    setRainProbabilityThreshold
  }
}
export default useConfigHook
