import clientService from '@/services/client.service'
import useNotificationHook from '@/shared/hook/useNotificationHook'
import storageService from '@/shared/services/storage.service'
import { HTTP_STATUS } from '@/shared/types/http.type'
import { Form } from 'antd'
import { useNavigate } from 'react-router-dom'
interface LoginForm {
  username: string
  password: string
}

const useLoginHook = () => {
  const [form] = Form.useForm<LoginForm>()
  const { showSuccess, showError } = useNotificationHook()
  const navigate = useNavigate()
  const handleLogin = async () => {
    const values = form.getFieldsValue()
    try {
      const response = await clientService.login(values)
      if (response.status === HTTP_STATUS.OK) {
        // login thành công
        /**
         * 1. Lưu thông tin vào context, localstorage
         * 2. Hiển thị thông báo
         * 3. Navigate
         */
        showSuccess('Đăng nhập thành công')
        navigate('/')
      } else {
        storageService.clear()
        showError('Tài khoản hoặc mật khẩu không chính xác')
      }
    } catch (e) {
      showError(`Lỗi server: ${e}`)
    }
  }
  return { handleLogin, form }
}
export default useLoginHook
