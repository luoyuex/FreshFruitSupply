import { request } from './request.js'

export function isPlaceholderPhone(phone) {
  return !phone || String(phone).startsWith('wx:')
}

function persistCustomerAuth(data) {
  uni.setStorageSync('customer_token', data.access_token)
  uni.setStorageSync('customer_id', data.customer?.id || '')
  uni.setStorageSync('verification_status', data.customer?.verification_status || 'unverified')
  if (!isPlaceholderPhone(data.customer?.phone)) {
    uni.setStorageSync('customer_phone', data.customer.phone)
  } else {
    uni.removeStorageSync('customer_phone')
  }
}

export function hasCustomerLogin() {
  return Boolean(uni.getStorageSync('customer_token'))
}

async function exchangeLoginCode(code) {
  if (!code) throw new Error('微信登录未返回 code')
  const data = await request({
    url: '/auth/wechat-login',
    method: 'POST',
    data: { code },
  })
  persistCustomerAuth(data)
  return data
}

export function loginWithWeChat() {
  return new Promise((resolve, reject) => {
    if (typeof wx === 'undefined' || !wx.login) {
      reject(new Error('请在微信小程序环境中登录'))
      return
    }
    wx.login({
      success: async (loginRes) => {
        try {
          console.log('[auth] account info', wx.getAccountInfoSync?.())
          console.log('[auth] wx login result', loginRes)
          resolve(await exchangeLoginCode(loginRes.code))
        } catch (err) {
          reject(err)
        }
      },
      fail: (err) => reject(new Error(err.errMsg || '微信登录失败')),
    })
  })
}

export function logoutCustomer() {
  uni.removeStorageSync('customer_token')
  uni.removeStorageSync('customer_id')
  uni.removeStorageSync('customer_phone')
  uni.removeStorageSync('verification_status')
  uni.removeStorageSync('fruit_quote_cart')
  uni.removeStorageSync('checkout_items')
  uni.removeStorageSync('selected_address')
}
