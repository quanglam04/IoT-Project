import type { DataSensor } from '@/shared/types/sensor.type'
import { io, type Socket } from 'socket.io-client'

class SocketService {
  private socket: Socket | null = null

  connect() {
    if (this.socket?.connected) {
      return this.socket
    }

    this.socket = io(import.meta.env.VITE_SOCKET_URL, {
      // auth: { token },
      transports: ['websocket']
    })

    this.socket.on('connect', () => {
      console.log('Socket connected')
    })

    this.socket.on('disconnect', () => {
      console.log('Socket disconnected')
    })

    this.socket.on('connect_error', (error) => {
      console.error('Connection error:', error)
    })

    return this.socket
  }

  disconnect() {
    this.socket?.disconnect()
    this.socket = null
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onReceiveDataFromSensor(callback: (data: DataSensor) => void) {
    this.socket?.on('sensor/data/push', callback)
  }
}

export default new SocketService()
