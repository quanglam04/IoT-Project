import axios, {
  type AxiosInstance,
  type AxiosRequestConfig,
  type AxiosResponse,
  type InternalAxiosRequestConfig
} from 'axios'

class _Http {
  private readonly instance: AxiosInstance

  constructor() {
    this.instance = axios.create({
      baseURL: import.meta.env.VITE_BACKEND_URL, // thường sẽ là localhost:8080//api/v1/
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json'
      }
    })

    // Config Request Interceptor
    this.instance.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        // Có thể thêm token vào đây
        // const token = localStorage.getItem('token')
        // if (token) {
        //   config.headers.Authorization = `Bearer ${token}`
        // }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Config Response Interceptor
    this.instance.interceptors.response.use(
      (response: AxiosResponse) => {
        return response
      },
      (error) => {
        // Xử lý lỗi response
        if (error.response?.status === 401) {
          // Redirect to login hoặc refresh token
          console.log('Unauthorized access')
        }
        return Promise.reject(error)
      }
    )
  }
  /**
   * @param T: định nghĩa kiểu mà API sẽ trả về ( xem ví dụ)
   * @param url: đường dãn API
   * @param config
   * @returns
   * Ví dụ sử dụng
   * const response = await http.get<ApiResponse<User[]>>('/users')
   * =============================================================
   * @description: API Login:
   * interface LoginRequest {
   *     username: string
   *     password: string
   * }
   * interface LoginResponse {
   *    message: string
   *    user: User
   *    accessToken: string
   *    refreshToken: string
   * }
   * credentials: LoginRequest
   * const response = await http.post<ApiResponse<LoginResponse>>('/auth/login',credentials)
   * ==============================================================
   * @description: API tạo mới
   * interface CreateUserRequest {
   *  username: string
   *  email: string
   *  password: string
   *  fullName: string
   * }
   * userData: CreateUserRequest
   * const response = await http.post<ApiResponse<User>>(/users', userData)
   * ==============================================================
   * @description: Trường hợp sử dụng biến Config truyền vào
   * const config: AxiosRequestConfig = {
   *    headers: {
   *        'Authorization': `Bearer ${token}`,
   *        'X-Custom-Header': 'some-value'
   *    }
   *  }
   * const response = await http.get<ApiResponse<User>>('/user/profile', config)
   */

  get<T>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.instance.get(url, config)
  }

  post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.instance.post(url, data, config)
  }

  put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.instance.put(url, data, config)
  }

  delete<T>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.instance.delete(url, config)
  }

  patch<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.instance.patch(url, data, config)
  }
}

const http = new _Http()

export default http
