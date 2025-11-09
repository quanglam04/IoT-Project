import { Request, Response } from 'express'
import User, { UserRole } from "../models/User"
import HTTPStatus from "../shared/constants/httpStatus"
import logger from "../utils/log"
import * as jwt from 'jsonwebtoken'
import { AuthRequest } from '../shared/types/util.type'


const login = async (req: Request, res: Response) => {
  const { username, password } = req.body
  logger.info(`User [${username}] đăng nhập vào hệ thống`)
  if (!username || !password) {
    return res.status(HTTPStatus.BAD_REQUEST).json({
      status: HTTPStatus.BAD_REQUEST,
      message: 'Vui lòng cung cấp đầy đủ tên đăng nhập và mật khẩu.'
    })
  }
  try {
    const user = await User.findOne({ username: username })
    if (!user) {
      return res.status(HTTPStatus.UNAUTHORIZED).json({
        status: HTTPStatus.UNAUTHORIZED,
        message: 'Tên đăng nhập hoặc mật khẩu không đúng.'
      })
    }
    const isPasswordValid = password === user.password
    if (!isPasswordValid) {
      return res.status(HTTPStatus.UNAUTHORIZED).json({
        status: HTTPStatus.UNAUTHORIZED,
        message: 'Tên đăng nhập hoặc mật khẩu không đúng.'
      })
    }

    // đầu tiên định cho chung mà đọc api design bảo chỉ 3 cái này nên tách ra nhé
    const Payload = { 
      id: user.id,
      username: user.username,
      role: user.role
    }
    const access_token = jwt.sign(Payload, process.env.JWT_SECRET as string, {
      expiresIn: '1d'
    })

    const userResponseData = {
      id: user.id,
      username: user.username,
      fullName: user.fullName,
      address: user.address,
      phoneNumber: user.phoneNumber,
      role: user.role
    }
    return res.status(HTTPStatus.OK).json({
      status: HTTPStatus.OK,
      message: 'Đăng nhập thành công',
      data: {
        access_token: access_token,
        user_info: userResponseData
      }
    })
  } catch (error) {
    console.error('Lỗi đăng nhập:', error)
    return res.status(HTTPStatus.INTERNAL_SERVER_ERROR).json({
      status: HTTPStatus.INTERNAL_SERVER_ERROR,
      message: 'Đã xảy ra lỗi hệ thống.'
    })
  }
}

const getListUser = async (req: AuthRequest, res: Response) => {
  logger.info('Lấy danh sách người dùng')
  try {
    const currentUserRole = (req.user as jwt.JwtPayload).role
    if(currentUserRole === UserRole.ADMIN){
      const listUser = await User.find().select('fullName address phoneNumber role')
      if (listUser.length) {
        return res.status(HTTPStatus.OK).json({
          status: HTTPStatus.OK,
          message: 'Lấy danh sách người dùng thành công',
          data: listUser
        })
      } else {
        return res.status(HTTPStatus.NO_CONTENT).json({
          status: HTTPStatus.NO_CONTENT,
          message: 'Danh sách người dùng hiện đang trống',
          data: listUser
        })
      }
    }
    else{
      return res.status(HTTPStatus.FORBIDDEN).json({
          status: HTTPStatus.FORBIDDEN,
          message: 'Bạn không có quyền hạn này',
        })
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } catch (e: any) {
    logger.error('Lỗi không thể lấy danh sách người dùng: ', e)
    return res.status(HTTPStatus.INTERNAL_SERVER_ERROR).json({
      status: HTTPStatus.INTERNAL_SERVER_ERROR,
      message: 'Lỗi server',
      data: null
    })
  }
}

export { login, getListUser }