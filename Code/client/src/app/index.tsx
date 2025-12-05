import { createRoot } from 'react-dom/client'
import './styles/index.css'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { StrictMode } from 'react'
import { router } from './router'
import { LoadingProvider } from '@/shared/context/LoadingContext'
import GlobalLoading from '@/shared/components/loading'

const appRouter = createBrowserRouter(router)

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <LoadingProvider>
      <GlobalLoading />
      <RouterProvider router={appRouter} />
    </LoadingProvider>
  </StrictMode>
)
