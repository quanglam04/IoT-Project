import { createContext, useState, type ReactNode } from 'react'

type LoadingContextType = {
  isLoading: boolean
  start: () => void
  finish: () => void
}

export const LoadingContext = createContext<LoadingContextType | undefined>(undefined)

export const LoadingProvider = ({ children }: { children: ReactNode }) => {
  const [isLoading, setLoading] = useState(false)

  const start = () => setLoading(true)
  const finish = () => setLoading(false)

  return <LoadingContext.Provider value={{ isLoading, start, finish }}>{children}</LoadingContext.Provider>
}
