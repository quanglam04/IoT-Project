class _StorageService {
  public set(key: string, value: string) {
    localStorage.setItem(key, value)
  }
  public get(key: string) {
    return localStorage.getItem(key)
  }
  public clearDataExcludeDataSensor() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('fullName')
    localStorage.removeItem('role')
  }
  public getAccessTokenFromLS = () => localStorage.getItem('access_token') || ''
}

const storageService = new _StorageService()

export default storageService
