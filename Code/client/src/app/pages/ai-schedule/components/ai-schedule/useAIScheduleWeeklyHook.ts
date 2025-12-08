import socketService from '@/services/socket.service'
import storageService from '@/shared/services/storage.service'
import type { TodaySchedule } from '@/shared/types/auth.type'
import { useEffect, useState } from 'react'

const useAIScheduleWeeklyHook = () => {
  const [dataSchedule, setDataSchedule] = useState<TodaySchedule[]>([])
  useEffect(() => {
    socketService.onReceiveScheduleFromAI((data: TodaySchedule[]) => {
      console.log(data)
      storageService.set('scheduleWeekly', JSON.stringify(data))
      setDataSchedule(data)
    })
  }, [])

  useEffect(() => {
    const data: TodaySchedule[] = storageService.get('scheduleWeekly')
      ? JSON.parse(storageService.get('scheduleWeekly') as string)
      : ''
    if (data) {
      setDataSchedule([...data])
    }
  }, [])

  return { dataSchedule }
}
export default useAIScheduleWeeklyHook
