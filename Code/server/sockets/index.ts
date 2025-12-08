import { Server } from 'socket.io'
import logger from '../utils/log'

/**
 * 
 * @param io Setup kết nối khi server và client chạy thì tự động connect lại
 */

export const setupSocket = (io: Server) => {
  // Middleware xác thực người dùng

  // Xử lý kết nối socket
  io.on('connection', (socket) => {
    // Lắng nghe sự kiện "disconnect"
    socket.on('disconnect', () => {
    })
  })
}