import { useState } from 'react'

const useHook = () => {
  const [selectedRange, setSelectedRange] = useState<string>('3d')

  const handleSelectTime = (value: string) => {
    setSelectedRange(value)
    // Call API
  }
  return { selectedRange, handleSelectTime }
}
export default useHook
