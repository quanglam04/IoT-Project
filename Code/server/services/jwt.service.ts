const tokenBlacklist = new Map<string, number>()
/**
 * Thêm token vào danh sách đen và lên lịch xóa nó khi hết hạn.
 * @param token Chuỗi JWT cần vô hiệu hóa.
 * @param exp Thời gian hết hạn của token (dạng Unix timestamp - giây).
 */
export const addToBlacklist = (token: string, exp: number): void => {
  const nowMs = Date.now()
  const expMs = exp * 1000
  if (expMs > nowMs) {
    const ttlMs = expMs - nowMs
    tokenBlacklist.set(token, expMs)
    setTimeout(() => {
      tokenBlacklist.delete(token)
    }, ttlMs)
  }
}

/**
 * Kiểm tra xem token có trong danh sách đen không.
 * @param token Chuỗi JWT.
 * @returns true nếu token bị vô hiệu hóa, false nếu hợp lệ.
 */
export const isBlacklisted = (token: string): boolean => {
  return tokenBlacklist.has(token)
}