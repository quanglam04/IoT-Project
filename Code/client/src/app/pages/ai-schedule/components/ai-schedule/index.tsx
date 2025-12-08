import { data } from './data'
import useAIScheduleWeeklyHook from './useAIScheduleWeeklyHook'

const AISchedule = () => {
  const { dataSchedule } = useAIScheduleWeeklyHook()
  console.log(dataSchedule)
  return (
    <div className='rounded-2xl bg-gradient-to-br from-blue-50 to-blue-100 p-6'>
      <div className='rounded-3xl border-2 border-gray-800 bg-white p-8 shadow-lg'>
        <h2 className='mb-8 text-2xl font-bold text-gray-800'>Lịch tưới theo tuần</h2>

        <div className='max-h-[500px] overflow-x-auto overflow-y-auto rounded-xl border border-gray-200'>
          <table className='w-full'>
            <thead className='sticky top-0 bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-md'>
              <tr>
                <th className='px-6 py-4 text-left text-sm font-semibold tracking-wide uppercase'>Ngày</th>
                <th className='px-6 py-4 text-left text-sm font-semibold tracking-wide uppercase'>Ca tưới</th>
                <th className='px-6 py-4 text-left text-sm font-semibold tracking-wide uppercase'>Thời gian tưới</th>
              </tr>
            </thead>
            <tbody className='divide-y divide-gray-200'>
              {dataSchedule.map((day, dayIndex) =>
                day.slots.map((slot, slotIndex) => (
                  <tr key={`${dayIndex}-${slotIndex}`} className='transition-colors hover:bg-blue-50'>
                    {slotIndex === 0 && (
                      <td
                        className='bg-blue-50 px-6 py-4 text-center font-bold text-gray-800'
                        rowSpan={day.slots.length}
                      >
                        <div className='flex flex-col'>
                          <span className='text-lg'>
                            {new Date(day.date).toLocaleDateString('vi-VN', {
                              day: '2-digit',
                              month: '2-digit'
                            })}
                          </span>
                          <span className='text-xs text-gray-600'>
                            {new Date(day.date).toLocaleDateString('vi-VN', {
                              weekday: 'long'
                            })}
                          </span>
                        </div>
                      </td>
                    )}
                    <td className='px-6 py-4'>
                      <div className='inline-flex items-center gap-3'>
                        <span className='inline-block w-32 rounded-full bg-green-100 px-4 py-2 text-center text-sm font-medium text-green-800'>
                          {slot.start} - {slot.end}
                        </span>
                        {slot.decision !== null && (
                          <span className='text-sm leading-none'>
                            {slot.decision ? '✅ Áp dụng ca tưới này' : '❌ Hoãn ca tưới này'}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className='px-6 py-4'>
                      <span className='inline-flex items-center rounded-md bg-blue-100 px-3 py-1 text-sm font-semibold text-blue-800'>
                        {slot.durationMin} phút
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default AISchedule
