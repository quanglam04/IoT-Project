import { createRoot } from 'react-dom/client'
import './styles/index.css'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { StrictMode } from 'react'
import { router } from './router'
import { GlobalProvider } from '@/shared/context/GlobalContext'

const appRouter = createBrowserRouter(router)

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <GlobalProvider>
      <RouterProvider router={appRouter} />
    </GlobalProvider>
  </StrictMode>
)
