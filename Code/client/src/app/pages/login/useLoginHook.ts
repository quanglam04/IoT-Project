import { Form } from 'antd'
interface LoginForm {
  username: string
  password: string
}

const useLoginHook = () => {
  const [form] = Form.useForm<LoginForm>()

  const handleLogin = async () => {
    // const values = form.getFieldsValue()
    // console.log(values)
    // try {
    //   const response = await clientService.login(values)
    //   if (response.status === HttpStatus.OK) {
    //     // login thành công
    //     /**
    //      * 1. Lưu thông tin vào context, localstorage
    //      * 2. Hiển thị thông báo
    //      * 3. Navigate
    //      */
    //     showSuccess('Đăng nhập thành công')
    //     navigate('/')
    //   } else {
    //     storageService.clear()
    //     showError('Tài khoản hoặc mật khẩu không chính xác')
    //   }
    // } catch (e) {
    //   showError(`Lỗi server: ${e}`)
    // }
  }
  return { handleLogin, form }
}
export default useLoginHook
