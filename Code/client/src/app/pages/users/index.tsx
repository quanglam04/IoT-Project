import useUserHook from './useUserHook'

const UserPage = () => {
  const { listUser } = useUserHook()

  return (
    <div className='rounded-2xl bg-gradient-to-br from-blue-50 to-blue-100 p-6'>
      <div className='rounded-3xl border-2 border-gray-800 bg-white p-8 shadow-lg'>
        <h2 className='mb-8 text-2xl font-bold text-gray-800'>Thông tin người dùng</h2>

        <div className='max-h-[600px] overflow-x-auto overflow-y-auto rounded-xl border border-gray-200'>
          <table className='w-full'>
            <thead className='sticky top-0 bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-md'>
              <tr>
                <th className='px-6 py-4 text-left text-sm font-semibold tracking-wide uppercase'>Email</th>
                <th className='px-6 py-4 text-left text-sm font-semibold tracking-wide uppercase'>Tên đầy đủ</th>
                <th className='px-6 py-4 text-left text-sm font-semibold tracking-wide uppercase'>Số điện thoại</th>
                <th className='px-6 py-4 text-left text-sm font-semibold tracking-wide uppercase'>Địa chỉ</th>
                <th className='px-6 py-4 text-left text-sm font-semibold tracking-wide uppercase'>
                  Vai trò trong hệ thống
                </th>
              </tr>
            </thead>
            <tbody className='divide-y divide-gray-200'>
              {listUser.map((user, index) => (
                <tr key={index} className='transition-colors hover:bg-blue-50'>
                  <td className='px-6 py-4'>
                    <span className='text-sm font-medium text-blue-600'>{user.email}</span>
                  </td>
                  <td className='px-6 py-4'>
                    <span className='text-sm font-semibold text-gray-800'>{user.fullName}</span>
                  </td>
                  <td className='px-6 py-4'>
                    <span className='text-sm text-gray-700'>{user.phoneNumber}</span>
                  </td>
                  <td className='px-6 py-4'>
                    <span className='text-sm text-gray-600'>{user.address}</span>
                  </td>
                  <td className='px-6 py-4'>
                    <span className='inline-flex items-center rounded-full bg-purple-100 px-3 py-1 text-sm font-medium text-purple-800'>
                      {user.role}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default UserPage
