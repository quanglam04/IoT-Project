import { useState } from 'react'
import { timeRanges } from '../../dummy'

const SelectTimeRange = () => {
  const [selectedRange, setSelectedRange] = useState('3d')

  return (
    <div className='w-fit rounded-3xl border-2 border-gray-800 bg-white p-6 shadow-lg'>
      <h3 className='mb-4 text-center text-xl font-bold'>
        Select Time
        <br />
        Range
      </h3>

      <div className='flex gap-3'>
        {timeRanges.map((range) => (
          <button
            key={range.value}
            onClick={() => setSelectedRange(range.value)}
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
