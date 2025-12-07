import type { RouteObject } from 'react-router-dom'
import NotFoundPage from './pages/not-found'
import PageLayoutPage from './layout/page-layout'
import DashBoardPage from './pages/dashboard'
import ChartPage from './pages/charts'
import AISchedulePage from './pages/ai-schedule'
import ManualControlPage from './pages/manual-control'
import LogPage from './pages/logs'
import ReportPage from './pages/reports'
import ConfigPage from './pages/config'
import UserPage from './pages/users'
import ProtectedRotes from '@/shared/components/protected-routes'
import LoginPage from './pages/login'
import NotificationPage from './pages/notification'
import RequireAdmin from '@/shared/components/require-admin'
import UpdateFirmwarePage from './pages/update-firmware'

const router: RouteObject[] = [
  {
    path: '/',
    element: (
      <ProtectedRotes>
        <PageLayoutPage />
      </ProtectedRotes>
    ),
    children: [
      {
        index: true,
        element: <DashBoardPage />
      },
      {
        path: 'chart-page',
        element: <ChartPage /> //user, admin
      },
      {
        path: 'ai-schedule-page',
        element: <AISchedulePage /> //user, admin
      },
      {
        path: 'manual-control-page',
        element: <ManualControlPage /> //user, admin
      },
      {
        path: 'log-page',
        element: <LogPage /> //user, admin
      },
      {
        path: 'report-page',
        element: <ReportPage /> // admin
      },
      {
        path: 'config-page',
        element: (
          <RequireAdmin>
            <ConfigPage />
          </RequireAdmin>
        ) // admin
      },
      {
        path: 'update-firmware',
        element: (
          <RequireAdmin>
            <UpdateFirmwarePage />
          </RequireAdmin>
        ) // admin
      },
      {
        path: 'user-page',
        element: (
          <RequireAdmin>
            <UserPage />
          </RequireAdmin>
        ) // admin
      },
      {
        path: 'notification-page',
        element: <NotificationPage /> //user, admin
      },
      {
        path: '*',
        element: <NotFoundPage />
      }
    ]
  },
  {
    path: '/login',
    element: <LoginPage />
  }
]

export { router }
