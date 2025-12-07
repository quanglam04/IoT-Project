import { Dayjs } from 'dayjs'
import type { DATE_FORMAT_ENUM } from '@/shared/types/date.type'

const formatDate = (date: Dayjs, format: DATE_FORMAT_ENUM) => {
  return date.format(format)
}

const getDateFormat = ({ onlyDate = true }: { onlyDate?: boolean }) => {
  const now = new Date()
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const year = now.getFullYear()
  if (onlyDate) return `${day}/${month}/${year}`
  return `${hours}:${minutes} ${day}/${month}/${year}`
}

export { formatDate, getDateFormat }
