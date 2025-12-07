import useNotificationHook from './useNotificationHook'

const NotificationPage = () => {
  const { handleMarkAllAsRead, notifications, isReadAll } = useNotificationHook()
  return (
    <div className='rounded-2xl bg-gradient-to-br from-blue-50 to-blue-100 p-6'>
      <div className='rounded-3xl border-2 border-gray-800 bg-white p-8 shadow-lg'>
        {/* Header with Mark as read button */}
        <div className='mb-8 flex items-center justify-between'>
          <h2 className='text-2xl font-bold'>Thông báo</h2>

          <button
            onClick={handleMarkAllAsRead}
            className='flex items-center gap-2 text-gray-600 transition-colors hover:text-gray-800'
          >
            <span>Đánh dấu đã đọc</span>
            <div className='flex h-5 w-5 cursor-pointer items-center justify-center rounded border-2 border-gray-400'>
              {isReadAll ? 'X' : ''}
            </div>
          </button>
        </div>

        <div className='space-y-4'>
          {notifications.map((notification) => (
            <div
              key={notification.id}
              className='flex items-center justify-between border-b border-gray-200 py-4 last:border-0'
            >
              <div className='flex items-center gap-8'>
                <span className='w-20 text-lg font-medium'>{notification.time}</span>
                <span className='text-lg'>{notification.message}</span>
              </div>

              {!notification.isRead && <div className='h-3 w-3 rounded-full bg-red-500'></div>}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default NotificationPage
