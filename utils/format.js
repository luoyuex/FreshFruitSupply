export function money(value) {
  const number = Number(value || 0)
  return number.toFixed(number % 1 === 0 ? 0 : 2)
}

export function statusLabel(status) {
  const labels = {
    in_stock: '现货充足',
    limited: '少量现货',
    out_of_stock: '暂时缺货',
    pending: '待确认',
    confirmed: '已确认',
    delivering: '配送中',
    completed: '已完成',
    cancelled: '已取消',
    unverified: '未认证',
    pending_review: '待审核',
    verified: '已认证',
    rejected: '未通过',
    failed: '邮件失败',
    sent: '已通知',
    unused: '未使用',
    used: '已使用',
    expired: '已过期',
  }
  return labels[status] || status || '未知'
}

export function todayText() {
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${month}月${day}日`
}


export function fruitIcon(name = '') {
  const iconMap = [
    ['苹果', '🍎'], ['橙', '🍊'], ['柑', '🍊'], ['香蕉', '🍌'], ['芒', '🥭'],
    ['葡萄', '🍇'], ['梨', '🍐'], ['桃', '🍑'], ['莓', '🍓'], ['瓜', '🍈'],
    ['榴莲', '🟡'], ['车厘子', '🍒'], ['樱桃', '🍒'], ['柠檬', '🍋'],
  ]
  return iconMap.find(([key]) => name.includes(key))?.[1] || '🍏'
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

// 券有效期展示：YYYY.MM.DD（现有 shortDateTime 无年份，不适合有效期）
export function dateText(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}.${month}.${day}`
}
