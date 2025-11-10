import { createContext, useContext } from 'react'

type GlobalContextType = {
  a: number
}

const GlobalContext = createContext<GlobalContextType | undefined>(undefined)

export const GlobalProvider = ({ children }: { children: React.ReactNode }) => {
  const aFake = 1
  const values = {
    a: aFake
  }

  return <GlobalContext.Provider value={values}>{children}</GlobalContext.Provider>
}

export const useGlobalContext = () => {
  const context = useContext(GlobalContext)
  if (context === undefined) {
    throw new Error('useGlobalContext must be used within a GlobalProvider')
  }
  return context
}
