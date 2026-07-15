import { request } from './request.js'

// 统一封装微信支付拉起：Mock 模式调开发接口模拟支付成功，真实模式走 uni.requestPayment。
// 返回 Promise，resolve 表示支付成功（订单/补差价已结算），reject 表示取消或失败。

function requestWechatPayment(params) {
  return new Promise((resolve, reject) => {
    if (typeof uni === 'undefined' || !uni.requestPayment) {
      reject(new Error('当前环境不支持微信支付'))
      return
    }
    uni.requestPayment({
      provider: 'wxpay',
      timeStamp: params.timeStamp,
      nonceStr: params.nonceStr,
      package: params.package,
      signType: params.signType || 'RSA',
      paySign: params.paySign,
      success: () => resolve(),
      fail: (err) => {
        const cancelled = /cancel/i.test(err.errMsg || '')
        reject(new Error(cancelled ? '支付已取消' : (err.errMsg || '支付失败')))
      },
    })
  })
}

// pay: PayResponse（含 out_trade_no 与 pay_params）
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
  await requestWechatPayment(params)
  // 真实模式：requestPayment 成功后，支付结果以微信服务器回调为准，
  // 前端此处仅代表用户完成付款动作，订单状态由后端回调推进。
}

// 为待支付订单发起首付支付并拉起收银台
export async function payOrder(orderId) {
  const pay = await request({ url: `/orders/${orderId}/pay`, method: 'POST' })
  await startPayment(pay)
  return pay
}
