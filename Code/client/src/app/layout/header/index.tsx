import storageService from '@/shared/services/storage.service'
import useHeaderHook from './useHeaderHook'

const Header = () => {
  const fullName = storageService.get('fullName') || 'Trịnh Quang Lâm'
  const { handleLogout } = useHeaderHook()
  return (
    <div className='flex w-full items-center justify-between px-4 py-2'>
      <div className='flex items-center space-x-2 rounded-lg border border-gray-300 bg-white px-4 py-2'>
        <span className='font-bold text-gray-700'>IoT Application - Group 6</span>
      </div>

      <div className='flex items-center gap-3'>
        {/* Username */}
        <div className='flex items-center space-x-2 rounded-lg border border-gray-300 bg-white px-4 py-2'>
          <div className='flex h-8 w-8 items-center justify-center rounded-full bg-blue-500 text-white'>👤</div>
          <span className='font-medium text-gray-700'>{fullName}</span>
        </div>

        {/* Đăng xuất */}
        <div className='flex cursor-pointer items-center space-x-2 rounded-lg border border-gray-300 bg-white px-4 py-2 transition-colors hover:bg-gray-50'>
          <div className='flex h-8 w-8 items-center justify-center rounded-full bg-blue-500 text-white'>🔒</div>
          <span
            className='font-medium text-gray-700'
            onClick={() => {
              handleLogout()
            }}
          >
            Đăng xuất
          </span>
        </div>
      </div>
    </div>
  )
}

export default Header
