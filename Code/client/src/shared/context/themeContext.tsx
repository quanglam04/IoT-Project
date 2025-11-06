import { createContext, useContext, useState } from 'react'
// -------------------------------------------------------------------------
// 1. Define những dữ liệu sẽ được lưu trong context
type DarkModeContextType = {
  isDarkMode: boolean
  toggleDarkMode: () => void
  setDarkMode: (value: boolean) => void
}
// -------------------------------------------------------------------------
// 2. Tạo Context
const DarkModeContext = createContext<DarkModeContextType | undefined>(undefined)
// -------------------------------------------------------------------------
// 3. Tạo provider bọc ngoài Component ( xử lý logic trong này)
export const DarkModeProvider = ({ children }: { children: React.ReactNode }) => {
  const [isDarkMode, setIsDarkMode] = useState(true)
  const toggleDarkMode = () => setIsDarkMode((prev) => !prev)
  const values = {
    isDarkMode: isDarkMode,
    toggleDarkMode: toggleDarkMode,
    setDarkMode: setIsDarkMode
  }
  return <DarkModeContext.Provider value={values}>{children}</DarkModeContext.Provider>
}
// -------------------------------------------------------------------------
// 4. Những chỗ nào cần sử dụng giá trị của context => Bọc ProviderComponent bên ngoài

/* 
<DarkModeProvider>
      <RouterProvider router={appRouter} />
</DarkModeProvider>

*/
// -------------------------------------------------------------------------
// 5. Tạo Hooks Custom dể lấy giá trị trong context ( hoặc lấy luôn bằng useContext(<Truyền tên Context>))

/*
const useDarkMode = () => {
  const context = useContext(DarkModeContext)
  if (!context) throw new Error('useDarkMode must be used within DarkModeProvider')
  return context
}
*/
// -------------------------------------------------------------------------
// 6. Lấy giá trị trong Context sử dụng Hook đã tạo ở trên

export const useTheme = () => useContext(DarkModeContext)
