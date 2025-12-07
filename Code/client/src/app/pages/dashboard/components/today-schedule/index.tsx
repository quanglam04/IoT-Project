import useTodayScheduleHook from './useTodayScheduleHook'

const WeeklySchedule = () => {
  const { todaySchedule } = useTodayScheduleHook()
  console.log(todaySchedule)
  return (
    <div className='flex h-full flex-col rounded-3xl border-2 border-gray-800 bg-white p-6 shadow-lg'>
      <h2 className='mb-2 text-2xl font-bold'>Lịch tưới ngày hôm nay</h2>

      <div className='flex max-h-[400px] flex-1 justify-center overflow-y-auto p-4'>
        <div className='w-full max-w-md space-y-4'>
          {todaySchedule.slots.map((slot, index) => (
            <div
              key={index}
              className='rounded-lg border-2 border-blue-200 bg-gradient-to-r from-blue-50 to-blue-100 p-4 shadow-md'
            >
              <div className='mb-2 flex items-center justify-between'>
                <span className='rounded-full bg-blue-600 px-3 py-1 text-sm font-semibold text-white'>
                  Ca {index + 1}
                </span>
                <span className='rounded-md bg-green-100 px-3 py-1 text-sm font-semibold text-green-800'>
                  {slot.durationMin} phút
                </span>
              </div>
              <div className='mt-3 flex items-center justify-center gap-2 text-lg font-bold text-gray-800'>
                <span className='rounded-md bg-white px-4 py-2 shadow-sm'>{slot.start}</span>
                <span className='text-blue-600'>→</span>
                <span className='rounded-md bg-white px-4 py-2 shadow-sm'>{slot.end}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default WeeklySchedule
