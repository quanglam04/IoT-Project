class _StorageService {
  public set(key: string, value: string) {
    localStorage.setItem(key, value)
  }
  public get(key: string) {
    localStorage.getItem(key)
  }
}

const storageService = new _StorageService()

export default storageService
