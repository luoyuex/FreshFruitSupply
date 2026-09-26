export function money(value) {
  const number = Number(value || 0)
  return number.toFixed(number % 1 === 0 ? 0 : 2)
}

export function qtyText(value) {
  const number = Number(value || 0)
  return String(parseFloat(number.toFixed(2)))
}

const STATUS_LABELS = {
  in_stock: '现货充足',
  limited: '少量现货',
  out_of_stock: '暂时缺货',
  unpaid: '待支付',
  pending: '待确认',
  confirmed: '已确认',
  delivering: '配送中',
  completed: '已完成',
  closed: '已关闭',
  cancelled: '已取消',
  unverified: '未认证',
  pending_review: '待审核',
  verified: '已认证',
  rejected: '未通过',
  revoked: '已取消',
  failed: '邮件失败',
  sent: '已通知',
  unused: '未使用',
  used: '已使用',
  expired: '已过期',
  pending_pay: '待支付',
  success: '已支付',
  refunded: '已退款',
  refund_failed: '退款失败',
}

export function statusLabel(status) {
  return STATUS_LABELS[status] || status || '未知'
}

const STATUS_TONES = {
  unpaid: 'warning',
  pending: 'warning',
  confirmed: 'primary',
  delivering: 'primary',
  completed: 'success',
  closed: 'info',
  cancelled: 'info',
  verified: 'success',
  unverified: 'info',
  pending_review: 'warning',
  revoked: 'info',
  rejected: 'danger',
}

export function statusTone(status) {
  return STATUS_TONES[status] || 'info'
}

export function shortDateTime(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  return `${month}-${day} ${hour}:${minute}`
}

export function dateTimeSec(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  const second = String(date.getSeconds()).padStart(2, '0')
  return `${date.getFullYear()}-${month}-${day} ${hour}:${minute}:${second}`
}

export function dateText(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${date.getFullYear()}.${month}.${day}`
}

// Date → YYYY-MM-DD，作为接口的 date 查询参数
export function isoDate(value = new Date()) {
  const date = value instanceof Date ? value : new Date(value)
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${date.getFullYear()}-${month}-${day}`
}

// key 即后端权限点（app/api/deps.py 的 ALL_PERMISSIONS）
export const ADMIN_NAV = [
  { key: 'orders', label: '订单管理', path: '/orders', icon: 'List' },
  { key: 'stats', label: '销售统计', path: '/stats', icon: 'DataAnalysis' },
  { key: 'verifications', label: '认证管理', path: '/verifications', icon: 'CircleCheck' },
  { key: 'fruits', label: '水果报价', path: '/fruits', icon: 'Goods' },
  { key: 'coupons', label: '卡券管理', path: '/coupons', icon: 'Ticket' },
  { key: 'users', label: '用户管理', path: '/users', icon: 'User' },
  { key: 'settings', label: '系统设置', path: '/settings', icon: 'Setting' },
  { key: 'settings', label: '公告管理', path: '/announcements', icon: 'Bell' },
]

// 授权面板里的可勾选项：公告管理复用 settings 权限点，故合并成一项说明
export const PERMISSION_OPTIONS = [
  { key: 'orders', label: '订单管理' },
  { key: 'stats', label: '销售统计' },
  { key: 'verifications', label: '认证管理' },
  { key: 'fruits', label: '水果报价' },
  { key: 'coupons', label: '卡券管理' },
  { key: 'users', label: '用户管理' },
  { key: 'settings', label: '系统设置（含公告）' },
]

// 与后端 deps.py 的 ROLE_PRESETS 一致：选角色即按此覆盖勾选，之后仍可逐项改
export const ROLE_PRESETS = {
  super_admin: PERMISSION_OPTIONS.map((item) => item.key),
  order_admin: ['orders'],
}

export function permissionLabels(keys) {
  return (keys || []).map((key) => PERMISSION_OPTIONS.find((item) => item.key === key)?.label || key)
}

export const ORDER_STATUSES = ['unpaid', 'pending', 'confirmed', 'delivering', 'completed', 'closed', 'cancelled']

// 后台可自行流转的目标状态（与小程序后台一致）
export const ORDER_TARGET_STATUSES = ['pending', 'confirmed', 'delivering', 'completed', 'cancelled', 'closed']

export const STOCK_STATUSES = ['in_stock', 'limited', 'out_of_stock']

export const COUPON_KINDS = [
  { value: 'discount', label: '满减券' },
  { value: 'reissue', label: '商品补送券' },
]

// 场景邮件类型，取值与后端 app/services/email.py 的 KIND_* 一一对应
export const NOTICE_KINDS = [
  { value: 'dispatch', label: '配货通知' },
  { value: 'updated', label: '改单通知' },
  { value: 'refund_customer', label: '客户取消退款' },
  { value: 'refund_admin', label: '后台退款' },
  { value: 'stray_payment', label: '关单后到账退回' },
]

export function noticeLabel(kind) {
  return NOTICE_KINDS.find((item) => item.value === kind)?.label || kind
}

export function addressText(order) {
  return `${order.province || ''}${order.city || ''}${order.district || ''}${order.detail_address || ''}`
}

export function roleLabel(role) {
  return role === 'super_admin' ? '超级管理员' : '订单管理员'
}
