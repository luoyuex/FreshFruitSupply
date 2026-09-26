import http from './request'

// ---- 会话 ----
export const login = (data) => http.post('/admin/login', data)
export const fetchMe = () => http.get('/admin/me')

// ---- 订单 ----
export const listOrders = (params) => http.get('/admin/orders', { params })
export const deliverySheet = (params) => http.get('/admin/delivery-sheet', { params })
export const updateOrderStatus = (orderId, status) => http.patch(`/admin/orders/${orderId}`, { status })
export const bulkUpdateOrderStatus = (orderIds, status) => (
  http.patch('/admin/orders/bulk-status', { order_ids: orderIds, status })
)
export const listOrderPayments = (orderId) => http.get(`/admin/orders/${orderId}/payments`)
export const refundOrder = (orderId, data) => http.post(`/admin/orders/${orderId}/refund`, data)
export const resendOrderNotice = (orderId, kind) => http.post(`/admin/orders/${orderId}/notify/${kind}`)

// ---- 销售统计 ----
export const salesStats = (params) => http.get('/admin/sales-stats', { params })

// ---- 商家认证 ----
export const listVerifications = (params) => http.get('/admin/verifications', { params })
export const revokeVerification = (id, data) => http.patch(`/admin/verifications/${id}`, data)

// ---- 水果与分类（列表走公开接口，与小程序后台一致）----
export const listPublicFruits = (params) => http.get('/fruits', { params })
export const createFruit = (data) => http.post('/admin/fruits', data)
export const updateFruit = (id, data) => http.patch(`/admin/fruits/${id}`, data)
export const listCategories = () => http.get('/admin/categories')
export const createCategory = (data) => http.post('/admin/categories', data)
export const updateCategory = (id, data) => http.patch(`/admin/categories/${id}`, data)

export function uploadImage(file) {
  const form = new FormData()
  form.append('file', file)
  return http.post('/admin/uploads', form)
}

// ---- 卡券 ----
export const listCouponTemplates = () => http.get('/admin/coupon-templates')
export const createCouponTemplate = (data) => http.post('/admin/coupon-templates', data)
export const updateCouponTemplate = (id, data) => http.patch(`/admin/coupon-templates/${id}`, data)
export const grantCoupon = (customerId, templateId) => (
  http.post(`/admin/customers/${customerId}/coupons`, { template_id: templateId })
)
export const listCustomerCoupons = (customerId) => http.get(`/admin/customers/${customerId}/coupons`)
export const deleteCustomerCoupon = (customerId, couponId) => (
  http.delete(`/admin/customers/${customerId}/coupons/${couponId}`)
)

// ---- 用户与管理员 ----
export const listAdminUsers = () => http.get('/admin/admin-users')
export const createAdminUser = (data) => http.post('/admin/admin-users', data)
export const updateAdminUser = (id, data) => http.patch(`/admin/admin-users/${id}`, data)
export const resetAdminPassword = (id, password) => http.patch(`/admin/admin-users/${id}/password`, { password })
export const deleteAdminUser = (id) => http.delete(`/admin/admin-users/${id}`)
export const changeMyPassword = (data) => http.post('/admin/me/password', data)
export const listCustomers = () => http.get('/admin/customers')

// ---- 设置与公告 ----
export const getDeliveryConfig = () => http.get('/admin/settings/delivery')
export const updateDeliveryConfig = (data) => http.patch('/admin/settings/delivery', data)
export const listAnnouncements = () => http.get('/admin/announcements')
export const createAnnouncement = (data) => http.post('/admin/announcements', data)
export const updateAnnouncement = (id, data) => http.patch(`/admin/announcements/${id}`, data)
export const deleteAnnouncement = (id) => http.delete(`/admin/announcements/${id}`)
