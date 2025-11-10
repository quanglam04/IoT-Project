import { useNavigate } from 'react-router-dom'
import { Button, Form, Input } from 'antd'
import useLoginHook from './useLoginHook'

const { Item: FormItem } = Form

const LoginPage = () => {
  const { handleLogin, form } = useLoginHook()
  const navigate = useNavigate()
  return (
    <div className='flex h-screen items-center justify-center bg-gray-50'>
      <div className='flex w-[400px] flex-col items-center justify-center rounded-2xl border border-gray-300 bg-white p-6 shadow-lg'>
        <Form form={form} layout='vertical' className='w-full'>
          <FormItem label='Tài khoản' name='username'>
            <Input className='!w-full' />
          </FormItem>

          <FormItem label='Mật khẩu' name='password'>
            <Input.Password className='!w-full' />
          </FormItem>

          <Button type='primary' block onClick={handleLogin}>
            Đăng nhập
          </Button>

          <div
            className='mt-2 cursor-pointer text-center hover:text-blue-300 hover:underline'
            onClick={() => navigate('/register')}
          >
            Chưa có tài khoản? Click vào đây để đăng ký
          </div>
        </Form>
      </div>
    </div>
  )
}

export default LoginPage
