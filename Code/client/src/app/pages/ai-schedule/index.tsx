import AISchedule from './components/ai-schedule'
import AISuggest from './components/ai-suggest'

const AISchedulePage = () => {
  return (
    <div className='rounded-2xl bg-gradient-to-br from-blue-50 to-blue-100 p-6'>
      <div className='space-y-6'>
        <AISchedule />
        <AISuggest />
      </div>
    </div>
  )
}

export default AISchedulePage
