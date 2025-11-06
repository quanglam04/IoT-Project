import { Dayjs } from 'dayjs'
import type { DATE_FORMAT_ENUM } from '@/shared/types/date.type'

const formatDate = (date: Dayjs, format: DATE_FORMAT_ENUM) => {
  return date.format(format)
}

export { formatDate }
