import { timeRanges } from '../../dummy'
import useHook from './useHook'

const SelectTimeRange = () => {
  const { handleSelectTime, selectedRange } = useHook()
  return (
    <div className='w-fit rounded-3xl border-2 border-gray-800 bg-white p-6 shadow-lg'>
      <h3 className='mb-4 text-center text-xl font-bold'>
        Chọn thời gian
        <br />
        Khoảng
      </h3>

      <div className='flex gap-3'>
        {timeRanges.map((range) => (
          <button
            key={range.value}
            onClick={() => handleSelectTime(range.value)}
            className={`rounded-xl px-8 py-3 text-lg font-semibold transition-colors ${
              selectedRange === range.value ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            } `}
          >
            {range.label}
          </button>
        ))}
      </div>
    </div>
  )
}

export default SelectTimeRange
