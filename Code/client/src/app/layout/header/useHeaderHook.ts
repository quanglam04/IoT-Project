import useNotificationHook from '@/shared/hook/useNotificationHook'
import storageService from '@/shared/services/storage.service'
import { useNavigate } from 'react-router-dom'

const useHeaderHook = () => {
  const navigate = useNavigate()
  const { showSuccess } = useNotificationHook()
  const handleLogout = () => {
    console.log('logout')
    navigate('/login')
    storageService.clearDataExcludeDataSensor()
    showSuccess('Đăng xuất thành công')
  }
  return { handleLogout }
}
export default useHeaderHook
