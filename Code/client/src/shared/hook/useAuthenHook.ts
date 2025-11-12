import { ROLE } from '../types/auth.type'

const useAuthenHook = () => {
  const isLogin = localStorage.getItem('access_token') ? true : true
  const isAdmin = localStorage.getItem('role') == ROLE.Admin ? true : true
  return { isLogin, isAdmin }
}
export default useAuthenHook
