import { decisions } from '../../dummy'

const RecentAIDecision = () => {
  return (
    <div className='h-full rounded-3xl border-2 border-gray-800 bg-white p-6 shadow-lg'>
      <h2 className='mb-6 text-2xl font-bold'>Quyết định của AI gần đây</h2>

      <div className='overflow-x-auto'>
        <table className='w-full'>
          <thead>
            <tr className='border-b-2 border-gray-200'>
              <th className='px-2 py-3 text-left font-semibold'>Thời gian</th>
              <th className='px-2 py-3 text-left font-semibold'>p(60m)</th>
              <th className='px-2 py-3 text-left font-semibold'>Hành động</th>
              <th className='px-2 py-3 text-left font-semibold'>Ghi chú</th>
            </tr>
          </thead>
          <tbody>
            {decisions.map((decision, index) => (
              <tr key={index} className='border-b border-gray-100'>
                <td className='px-2 py-3'>{decision.time}</td>
                <td className='px-2 py-3'>{decision.p60m}</td>
                <td className='px-2 py-3'>{decision.action}</td>
                <td className='px-2 py-3 text-sm text-gray-600'>{decision.note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default RecentAIDecision
