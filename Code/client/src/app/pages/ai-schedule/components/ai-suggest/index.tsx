import { suggestedActions } from '../../dummy'

const AISuggest = () => {
  return (
    <div className='max-w-3xl rounded-3xl border-2 border-gray-800 bg-white p-6 shadow-lg'>
      <h2 className='mb-6 text-2xl font-bold'>Hành động được AI đề xuất</h2>

      <div className='overflow-x-auto'>
        <table className='w-full'>
          <thead>
            <tr className='border-b-2 border-gray-300'>
              <th className='px-6 py-4 text-center text-lg font-bold'>Thời gian</th>
              <th className='px-6 py-4 text-center text-lg font-bold'>p</th>
              <th className='px-6 py-4 text-center text-lg font-bold'>Hành động</th>
            </tr>
          </thead>
          <tbody>
            {suggestedActions.map((action, index) => (
              <tr key={index} className='border-b border-gray-200'>
                <td className='px-6 py-4 text-center'>{action.time}</td>
                <td className='px-6 py-4 text-center'>{action.probability}</td>
                <td className='px-6 py-4 text-center'>{action.action}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default AISuggest
