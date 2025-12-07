import socketService from '@/services/socket.service'
import storageService from '@/shared/services/storage.service'
import type { AIPrediction } from '@/shared/types/sensor.type'
import { useEffect, useState } from 'react'

const useAIPredictionHook = () => {
  const [rainProbability, setRainProbability] = useState<number>(0)
  const [suggestion, setSuggestion] = useState<string>('')
  useEffect(() => {
    console.log('kết nối socket')
    socketService.onReceiveSuggestionFromAI((data: AIPrediction) => {
      setRainProbability(data.chanceOfRain)
      setSuggestion(data.recommendation)
      storageService.set('aiPredictData', JSON.stringify(data))
    })
  }, [])

  useEffect(() => {
    const data: AIPrediction = storageService.get('aiPredictData')
      ? JSON.parse(storageService.get('aiPredictData') as string)
      : ''
    if (data) {
      setRainProbability(data.chanceOfRain)
      setSuggestion(data.recommendation)
    }
  }, [])

  return { rainProbability, suggestion }
}
export default useAIPredictionHook
