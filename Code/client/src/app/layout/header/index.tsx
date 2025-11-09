const Header = () => {
  return (
    <>
      <div className='flex items-center space-x-2 rounded-lg border border-gray-300 bg-white px-4 py-2'>
        <div className='flex h-8 w-8 items-center justify-center rounded-full bg-blue-500 text-white'>👤</div>
        <span className='font-medium text-gray-700'>Trịnh Quang Lâm</span>
      </div>
      <div className='mx-2 flex items-center space-x-2 rounded-lg border border-gray-300 bg-white px-4 py-2'>
        <div className='flex h-8 w-8 items-center justify-center rounded-full bg-blue-500 text-white'>🔒</div>
        <span className='font-medium text-gray-700'>Đăng xuất</span>
      </div>
    </>
  )
}

export default Header
