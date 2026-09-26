import axios from 'axios'

const TOKEN_KEY = 'web_admin_token'

export function readToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  timeout: 20000,
})

http.interceptors.request.use((config) => {
  const token = readToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

function extractMessage(error, fallback) {
  const detail = error.response?.data?.detail ?? error.response?.data?.message
  if (!detail) return fallback
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join('；')
  return detail
}

http.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      clearToken()
      if (!window.location.hash.startsWith('#/login')) window.location.hash = '#/login'
      return Promise.reject(new Error('登录已过期，请重新登录'))
    }
    return Promise.reject(new Error(extractMessage(error, '请求失败')))
  },
)

export default http
