import { Request } from 'express'
import * as jwt from 'jsonwebtoken'

export interface AuthRequest extends Request {
  user?: string | jwt.JwtPayload
}