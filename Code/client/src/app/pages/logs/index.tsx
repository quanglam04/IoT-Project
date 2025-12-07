import useLogHook from './useLogHook'

const LogPage = () => {
  const { logs } = useLogHook()
  return (
    <div className='rounded-2xl bg-gradient-to-br from-blue-50 to-blue-100 p-6'>
      <div className='rounded-3xl border-2 border-gray-800 bg-white p-8 shadow-lg'>
        <h2 className='mb-8 text-2xl font-bold text-gray-800'>Nhật ký hoạt động</h2>

        <div className='max-h-[600px] overflow-x-auto overflow-y-auto rounded-xl border border-gray-200'>
          <table className='w-full'>
            <thead className='sticky top-0 bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-md'>
              <tr>
                <th className='px-6 py-4 text-left text-sm font-semibold tracking-wide uppercase'>Thời gian</th>
                <th className='px-6 py-4 text-left text-sm font-semibold tracking-wide uppercase'>Tác nhân</th>
                <th className='px-6 py-4 text-left text-sm font-semibold tracking-wide uppercase'>Sự kiện</th>
                <th className='px-6 py-4 text-left text-sm font-semibold tracking-wide uppercase'>Ghi chú</th>
              </tr>
            </thead>
            <tbody className='divide-y divide-gray-200'>
              {logs.map((log, index) => (
                <tr key={index} className='transition-colors hover:bg-blue-50'>
                  <td className='px-6 py-4'>
                    <span className='text-sm font-medium text-gray-700'>{log.createdAt}</span>
                  </td>
                  <td className='px-6 py-4'>
                    <span className='inline-flex items-center rounded-full bg-blue-100 px-3 py-1 text-sm font-medium text-blue-800'>
                      {log.actor}
                    </span>
                  </td>
                  <td className='px-6 py-4'>
                    <span className='inline-flex items-center rounded-md bg-green-100 px-3 py-1 text-sm font-semibold text-green-800'>
                      {log.event}
                    </span>
                  </td>
                  <td className='px-6 py-4'>
                    <span className='text-sm text-gray-600'>{log.details}</span>
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

export default LogPage
