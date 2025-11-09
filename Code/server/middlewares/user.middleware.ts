import { Response, NextFunction } from 'express'
import HTTPStatus from '../shared/constants/httpStatus'
import * as jwt from 'jsonwebtoken'
import { AuthRequest } from '../shared/types/util.type'

const JWT_SECRET = process.env.JWT_SECRET || 'fallback_secret_key'

export const authenticateToken = (req: AuthRequest, res: Response, next: NextFunction) => {
  const authHeader = req.headers['authorization']
  const token = authHeader && authHeader.split(' ')[1]
  if (token == null) {
    return res.status(HTTPStatus.UNAUTHORIZED).json({
      status: HTTPStatus.UNAUTHORIZED,
      message: 'Yêu cầu Access Token. Truy cập bị từ chối.'
    })
  }

  jwt.verify(token, JWT_SECRET, (err, user) => {
    if (err) {
      return res.status(HTTPStatus.UNAUTHORIZED).json({
        status: HTTPStatus.UNAUTHORIZED,
        message: 'Access Token không hợp lệ hoặc đã hết hạn.',
        data: null
      })
    }


    req.user = user
    next()
  })
}