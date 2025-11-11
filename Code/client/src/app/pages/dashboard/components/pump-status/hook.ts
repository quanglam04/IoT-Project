import microcontrollerService from '@/services/microcontroller.service'
import useNotificationHook from '@/shared/hook/useNotificationHook'
import { HTTP_STATUS } from '@/shared/types/http.type'
import { useState } from 'react'

const useHook = () => {
  const [open, setOpen] = useState<boolean>(false)
  const { showSuccess } = useNotificationHook()
  const handleOnClick = async () => {
    const response = await microcontrollerService.changeStatusPump(open)
    if (response.status == HTTP_STATUS.OK) {
      if (open) showSuccess('Tắt bơm thành công')
      else showSuccess('Bật bơm thành công')
      setOpen((prev) => !prev)
    }
  }
  return { open, handleOnClick }
}
export default useHook
