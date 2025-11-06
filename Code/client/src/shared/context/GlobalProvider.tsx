import type { ReactNode } from 'react'
import { AuthProvider } from './AuthContext'
import { DarkModeProvider } from './themeContext'

type Props = {
  children: ReactNode
}

const GlobalProvider = ({ children }: Props) => {
  return (
    <AuthProvider>
      <DarkModeProvider>{children}</DarkModeProvider>
    </AuthProvider>
  )
}
export default GlobalProvider

/**
 * dùng globalProvider bọc ngoài app
 * khi dùng chỉ cần
 * {theme} = useTheme()
 * {access_token} = useAuth()
 */
