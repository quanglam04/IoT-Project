import { createContext, useContext, useState } from 'react'

type AuthContextType = {
  access_token: string
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const access_token = '123'
  const values = {
    access_token: access_token
  }

  return <AuthContext.Provider value={values}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)
