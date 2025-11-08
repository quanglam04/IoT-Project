// src/sockets/index.ts
import { Server } from 'socket.io'
import logger from '../utils/log'


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