import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  withCredentials: false, // troque para true se usar cookies (ver nota)
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export const login = async (email, password) => {
  const { data } = await api.post('/auth/login', { email, password })
  // espere algo como: { access_token: '...', user: {...} }
  return data
}

export default api
