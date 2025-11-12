interface Menu {
  title: string
  navigateTo: string
  requireAdmin: boolean
}

const listMenu: Menu[] = [
  { title: 'Dashboard', navigateTo: '/', requireAdmin: false },
  { title: 'Charts', navigateTo: '/chart-page', requireAdmin: false },
  { title: 'AI Schedule', navigateTo: '/ai-schedule-page', requireAdmin: false },
  { title: 'Manual Control', navigateTo: '/manual-control-page', requireAdmin: false },
  { title: 'Logs', navigateTo: '/log-page', requireAdmin: true },
  { title: 'Reports', navigateTo: '/report-page', requireAdmin: true },
  { title: 'Config', navigateTo: '/config-page', requireAdmin: true },
  { title: 'Users', navigateTo: '/user-page', requireAdmin: true },
  { title: 'Notification', navigateTo: '/notification-page', requireAdmin: false }
]
export { listMenu }
