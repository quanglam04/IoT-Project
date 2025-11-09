import { io } from 'socket.io-client'

const useSocket = () => {
  const socket = io(import.meta.env.VITE_BACKEND_URL)
  return { socket }
}
export default useSocket
