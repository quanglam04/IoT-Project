import { useState } from 'react'

const useNotificationHook = () => {
  const [isReadAll, setIsReadAll] = useState<boolean>(false)
  const [notifications, setNotifications] = useState([
    {
      id: 1,
      time: '08:00',
      message: 'AI hoãn tưới (p=0.82)',
      isRead: true
    },
    {
      id: 2,
      time: '10:00',
      message: 'Đất khô, tưới 20m',
      isRead: false
    },
    {
      id: 3,
      time: '14:00',
      message: 'ESP32 disconnected',
      isRead: false
    }
  ])

  const handleMarkAllAsRead = () => {
    setNotifications(notifications.map((notif) => ({ ...notif, isRead: true })))
    setIsReadAll(true)
    console.log(`isReadAll : ${isReadAll}`)
  }

  return { handleMarkAllAsRead, notifications, setNotifications, isReadAll }
}
export default useNotificationHook
