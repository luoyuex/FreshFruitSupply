import { request } from './request.js'

export const ADMIN_NAV_ITEMS = [
  { key: 'orders', label: '订单', url: '/pages/admin/orders/index' },
  { key: 'stats', label: '统计', url: '/pages/admin/stats/index' },
  { key: 'verifications', label: '认证', url: '/pages/admin/verifications/index' },
  { key: 'fruits', label: '报价', url: '/pages/admin/fruits/index' },
  { key: 'coupons', label: '卡券', url: '/pages/admin/coupons/index' },
  { key: 'users', label: '用户', url: '/pages/admin/users/index' },
  { key: 'settings', label: '设置', url: '/pages/admin/settings/index' },
]

export function getAdminPermissions() {
  try {
    return JSON.parse(uni.getStorageSync('admin_permissions') || '[]')
  } catch (error) {
    return []
  }
}

export function getAdminUser() {
  try {
    return JSON.parse(uni.getStorageSync('admin_user') || 'null')
  } catch (error) {
    return null
  }
}

export function getAdminToken() {
  return uni.getStorageSync('admin_token') || ''
}

export function persistAdminSession(data) {
  if (data.access_token) {
    uni.setStorageSync('admin_token', data.access_token)
  }
  uni.setStorageSync('admin_user', JSON.stringify(data.admin || null))
  uni.setStorageSync('admin_permissions', JSON.stringify(data.permissions || []))
}

export function clearAdminSession() {
  uni.removeStorageSync('admin_token')
  uni.removeStorageSync('admin_user')
  uni.removeStorageSync('admin_permissions')
}

export function hasAdminPermission(permission) {
  return getAdminPermissions().includes(permission)
}

export function visibleAdminNavItems() {
  const permissions = getAdminPermissions()
  return ADMIN_NAV_ITEMS.filter((item) => permissions.includes(item.key))
}

export function redirectIfNoPermission(permission) {
  if (hasAdminPermission(permission)) return false
  uni.showToast({ title: '无权限访问', icon: 'none' })
  setTimeout(() => uni.redirectTo({ url: '/pages/admin/orders/index' }), 600)
  return true
}

export function goAdminNav(item) {
  uni.redirectTo({ url: item.url })
}

export async function refreshAdminSession() {
  if (!getAdminToken()) return false
  try {
    const data = await request({ url: '/admin/me', admin: true })
    persistAdminSession(data)
    return true
  } catch (error) {
    clearAdminSession()
    return false
  }
}

export async function openAdminHome() {
  const ok = await refreshAdminSession()
  uni.navigateTo({ url: ok ? '/pages/admin/orders/index' : '/pages/admin/login/index' })
}
