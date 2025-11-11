import { ROLE } from '../types/auth.type'

const useAuthenHook = () => {
  const isLogin = localStorage.getItem('access_token') ? true : false
  const isAdmin = localStorage.getItem('role') == ROLE.Admin ? true : false
  return { isLogin, isAdmin }
}
export default useAuthenHook
