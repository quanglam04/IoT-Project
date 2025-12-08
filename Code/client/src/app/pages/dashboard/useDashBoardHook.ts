import microcontrollerService from '@/services/microcontroller.service'
import mqttClientService from '@/services/mqtt.service'
import useNotificationHook from '@/shared/hook/useNotificationHook'
import { HTTP_STATUS } from '@/shared/types/http.type'
import { useEffect, useState } from 'react'

const useDashBoardHook = () => {
  const { showSuccess } = useNotificationHook()
  const [open, setOpen] = useState<boolean>(false)

  const handleOnClick = async () => {
    const response = await microcontrollerService.changeStatusPump(open)
    if (response.status == HTTP_STATUS.OK) {
      if (open) showSuccess('Tắt bơm thành công')
      else showSuccess('Bật bơm thành công')
      setOpen((prev) => !prev)
    }
  }

  useEffect(() => {
    mqttClientService.subscribe('device/pump/status', (message: string) => {
      const { pump } = JSON.parse(message)
      if (pump === 'ON') {
        setOpen(true)
      } else {
        setOpen(false)
      }
    })
  }, [open, showSuccess])

  return { open, handleOnClick }
}
export default useDashBoardHook
