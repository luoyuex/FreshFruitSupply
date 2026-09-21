import { request } from './request.js'

// 统一封装 B2b 门店助手支付（wx.requestCommonPayment）：
// Mock 模式调开发接口模拟支付成功，真实模式带最新 wx.login code 换支付参数后拉起收银台。
// 返回 Promise，resolve 表示支付动作完成（订单状态以后端查单/通知结算为准），reject 表示取消或失败。

// 取最新 wx.login code：后端用它现场换 session_key 生成支付用户态签名（保证签名时 session_key 必然有效）
function getWxLoginCode() {
  return new Promise((resolve, reject) => {
    uni.login({
      provider: 'weixin',
      success: (res) => {
        if (res.code) resolve(res.code)
        else reject(new Error(res.errMsg || '微信登录失败'))
      },
      fail: (err) => reject(new Error(err.errMsg || '微信登录失败')),
    })
  })
}

// B2b 支付：uni-app 无封装，直接调微信基础库的 wx.requestCommonPayment
function requestCommonPayment(params) {
  return new Promise((resolve, reject) => {
    if (typeof wx === 'undefined' || !wx.requestCommonPayment) {
      reject(new Error('当前微信版本不支持 B2b 支付，请升级微信'))
      return
    }
    wx.requestCommonPayment({
      signData: params.signData,
      mode: params.mode || 'retail_pay_goods',
      paySig: params.paySig,
      signature: params.signature,
      success: () => resolve(),
      fail: (err) => {
        const cancelled = /cancel/i.test(err.errMsg || '')
        reject(new Error(cancelled ? '支付已取消' : (err.errMsg || `支付失败(${err.errCode || ''})`)))
      },
    })
  })
}

// 真实模式下支付结果是异步结算的：前端支付动作完成后主动查单兜底，
// 避免「提示支付成功但订单仍是待支付」。
const SYNC_ATTEMPTS = 6
const SYNC_INTERVAL_MS = 1000

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function waitForSettlement(orderId) {
  for (let attempt = 0; attempt < SYNC_ATTEMPTS; attempt += 1) {
    const order = await request({ url: `/orders/${orderId}/pay/sync`, method: 'POST' })
    if (order && order.status && order.status !== 'unpaid') return order
    if (attempt < SYNC_ATTEMPTS - 1) await delay(SYNC_INTERVAL_MS)
  }
  const err = new Error('支付结果确认中，请稍后在“我的订单”查看')
  err.code = 'PAY_SETTLE_PENDING'
  throw err
}

// pay: PayResponse（pay_params 为后端签好的 B2b 支付参数；Mock 模式带 mock 标记）
// 成功后 resolve；Mock 模式在支付“成功”后调 mock-success 驱动后端结算。
export async function startPayment(pay) {
  const params = pay?.pay_params || {}
  if (params.mock) {
    // Mock 模式：无真实收银台，直接请求后端标记该笔流水支付成功
    await request({
      url: '/payments/dev/mock-success',
      method: 'POST',
      data: { out_trade_no: pay.out_trade_no || params.out_trade_no },
    })
    return
  }
  await requestCommonPayment(params)
  // 真实模式：requestCommonPayment 成功仅代表用户完成付款动作，订单状态以微信通知为准，
  // 这里轮询查单接口直到后端结算完成
  if (pay?.order_id) await waitForSettlement(pay.order_id)
}

// 为待支付订单发起支付并拉起收银台（携带最新 wx.login code 供后端签名）
export async function payOrder(orderId) {
  const wxLoginCode = await getWxLoginCode()
  const pay = await request({
    url: `/orders/${orderId}/pay`,
    method: 'POST',
    data: { wx_login_code: wxLoginCode },
  })
  await startPayment(pay)
  return pay
}
