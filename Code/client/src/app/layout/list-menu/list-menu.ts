interface Menu {
  title: string
  navigateTo: string
  requireAdmin: boolean
}

const listMenu: Menu[] = [
  { title: 'Tổng quan', navigateTo: '/', requireAdmin: false },
  { title: 'Biểu đồ', navigateTo: '/chart-page', requireAdmin: false },
  { title: 'Lịch tưới tự động', navigateTo: '/ai-schedule-page', requireAdmin: false },
  { title: 'Nhật ký', navigateTo: '/log-page', requireAdmin: true },
  { title: 'Báo cáo', navigateTo: '/report-page', requireAdmin: false },
  { title: 'Cập nhật Firmware', navigateTo: '/update-firmware', requireAdmin: true },
  { title: 'Người dùng', navigateTo: '/user-page', requireAdmin: true },
  { title: 'Thông báo', navigateTo: '/notification-page', requireAdmin: false }
]
export { listMenu }
