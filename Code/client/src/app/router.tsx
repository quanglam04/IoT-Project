import type { RouteObject } from 'react-router-dom'
import Home from './pages/home'
import NotFoundPage from './pages/not-found'

const router: RouteObject[] = [
  {
    path: '/',
    children: [
      {
        index: true,
        element: <Home />
      },
      {
        path: '*',
        element: <NotFoundPage />
      }
    ]
  }
]

export { router }
