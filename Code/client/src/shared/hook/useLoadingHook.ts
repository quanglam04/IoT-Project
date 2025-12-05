import { useContext } from 'react'
import { LoadingContext } from '../context/LoadingContext'

const useLoadingHook = () => {
  const ctx = useContext(LoadingContext)
  if (!ctx) throw new Error('useLoadingHook must be used inside <LoadingProvider>')
  return ctx
}

export default useLoadingHook
