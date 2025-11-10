import { activityLogs } from './dummy'

const LogPage = () => {
  return (
    <div className='rounded-2xl bg-gradient-to-br from-blue-50 to-blue-100 p-6'>
      <div className='rounded-3xl border-2 border-gray-800 bg-white p-8 shadow-lg'>
        <h2 className='mb-8 text-3xl font-bold'>Nhật ký hoạt động</h2>

        <div className='overflow-x-auto'>
          <table className='w-full'>
            <thead>
              <tr className='border-b-2 border-gray-300'>
                <th className='px-4 py-4 text-left text-lg font-bold'>Thời gian</th>
                <th className='px-4 py-4 text-left text-lg font-bold'>Tác nhân</th>
                <th className='px-4 py-4 text-left text-lg font-bold'>Sự kiện</th>
                <th className='px-4 py-4 text-left text-lg font-bold'>Ghi chú</th>
              </tr>
            </thead>
            <tbody>
              {activityLogs.map((log, index) => (
                <tr key={index} className='border-b border-gray-200'>
                  <td className='px-4 py-4'>{log.time}</td>
                  <td className='px-4 py-4'>{log.actor}</td>
                  <td className='px-4 py-4'>{log.event}</td>
                  <td className='px-4 py-4'>{log.note}</td>
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
