interface Menu {
  title: string
  navigateTo: string
}

const listMenu: Menu[] = [
  { title: 'Dashboard', navigateTo: '/' },
  { title: 'Charts', navigateTo: '/chart-page' },
  { title: 'AI Schedule', navigateTo: '/ai-schedule-page' },
  { title: 'Manual Control', navigateTo: '/manual-control-page' },
  { title: 'Logs', navigateTo: '/log-page' },
  { title: 'Reports', navigateTo: '/report-page' },
  { title: 'Config', navigateTo: '/config-page' },
  { title: 'Users', navigateTo: '/user-page' },
  { title: 'Notification', navigateTo: '/notification-page' }
]
export { listMenu }
