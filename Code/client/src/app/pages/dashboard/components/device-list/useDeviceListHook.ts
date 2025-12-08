import socketService from '@/services/socket.service'
import { useEffect, useState } from 'react'

const useDeviceListHook = () => {
  const [count, setCount] = useState<number>(0)
  console.log('count device: ', count)
  useEffect(() => {
    socketService.onDeviceStatus((data: number) => {
      setCount(data)
    })
  }, [count, setCount])
  return { count }
}
export default useDeviceListHook
