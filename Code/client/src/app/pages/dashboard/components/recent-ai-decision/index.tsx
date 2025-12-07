import useRecentAIDecisionHook from './useRecentAIDecisionHook'

const RecentAIDecision = () => {
  const { recentAIDecision } = useRecentAIDecisionHook()
  console.log('recentAI::', recentAIDecision)
  return (
    <div className='h-full rounded-3xl border-2 border-gray-800 bg-white p-6 shadow-lg'>
      <h2 className='mb-6 text-2xl font-bold'>Quyết định của AI gần đây</h2>

      <div className='max-h-[400px] overflow-y-auto rounded-2xl'>
        <table className='w-full'>
          <thead className='sticky top-0 bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-md'>
            <tr className='sticky top-0 border-b-2 border-gray-200'>
              <th className='px-2 py-3 text-left font-semibold tracking-wide'>Thời gian</th>
              <th className='px-2 py-3 text-left font-semibold tracking-wide'>Hành động</th>
              <th className='px-2 py-3 text-left font-semibold tracking-wide'>Lý do</th>
            </tr>
          </thead>
          <tbody className='divide-y divide-gray-200'>
            {recentAIDecision.map((decision, index) => (
              <tr key={index} className='border-b border-gray-100'>
                <td className='px-2 py-3 text-sm'>{decision.date}</td>
                <td className='px-2 py-3 text-sm'>{decision.shoudIrrigate ? 'Tưới' : 'Hoãn tưới'}</td>
                <td className='px-2 py-3 text-sm text-gray-600'>{decision.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default RecentAIDecision
