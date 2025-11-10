import { ROLE } from '../types/auth.type'

const useAuthenHook = () => {
  // const isLogin = localStorage.getItem('access_token') ? true : false
  // const isAdmin = localStorage.getItem('role') == ROLE.Admin ? true : false
  const isLogin = true
  const isAdmin = true
  return { isLogin, isAdmin }
}
export default useAuthenHook
