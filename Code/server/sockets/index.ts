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
    logger.info(`Một client đã kết nối: ${socket.id}`)

    // Lắng nghe sự kiện "disconnect"
    socket.on('disconnect', () => {
      logger.info(`Client đã ngắt kết nối: ${socket.id}`)
    })
  })
}