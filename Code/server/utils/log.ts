import { createLogger, format, transports } from 'winston'

const { combine, timestamp, printf, colorize } = format

const logFormat = printf(({ level, message, timestamp, stack }) => {
  return `${timestamp} [${level}]: ${stack || message}`
})

const logger = createLogger({
  level: 'info',
  format: combine(
    timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
    process.env.NODE_ENV !== 'production' ? colorize() : format.uncolorize(),
    format.errors({ stack: true }),
    logFormat
  ),
  transports: [new transports.Console()]
})

export default logger
