import { ref } from 'vue'
import { request } from './request.js'
import { payOrder } from './pay.js'

// 订单操作共享逻辑：订单列表页与订单详情页共用的支付、取消、编辑提示与地址拼接。
// 传入 onChanged 回调（操作成功后刷新数据），返回可直接在 <script setup> 解构使用的响应式方法集。

export function createOrderActions({ onChanged } = {}) {
  const paying = ref(false)
  const cancelling = ref(false)

  async function reload() {
    if (onChanged) await onChanged()
  }

  async function payOrderNow(order) {
    if (paying.value) return
    paying.value = true
    try {
      await payOrder(order.id)
      uni.showToast({ title: '支付成功', icon: 'success' })
      await reload()
    } catch (err) {
      if (err.code === 'PAY_SETTLE_PENDING') {
        // 付款动作已完成但后端尚未确认：提示后刷新，避免误报失败
        uni.showToast({ title: err.message, icon: 'none' })
        await reload()
        return
      }
      // 支付取消/失败：订单留在“待支付”，不弹错误打断
      if (err.message && err.message !== '支付已取消') {
        uni.showToast({ title: err.message, icon: 'none' })
      }
    } finally {
      paying.value = false
    }
  }

  function cancelOrder(order) {
    const paid = order.status !== 'unpaid'
    uni.showModal({
      title: paid ? '取消并退款' : '取消订单',
      content: paid
        ? '取消后将原路退还已支付的款项，确认取消该订单？'
        : '确认取消该待支付订单？',
      success: async (res) => {
        if (!res.confirm) return
        if (cancelling.value) return
        cancelling.value = true
        uni.showLoading({ title: paid ? '退款处理中...' : '取消中...', mask: true })
        try {
          await request({ url: `/orders/${order.id}/cancel`, method: 'POST' })
          uni.hideLoading()
          uni.showToast({ title: paid ? '已取消，退款处理中' : '订单已取消', icon: 'none' })
          await reload()
        } catch (err) {
          uni.hideLoading()
          uni.showToast({ title: err.message || '取消失败', icon: 'none' })
        } finally {
          cancelling.value = false
        }
      },
    })
  }

  // 商户尚未确认的订单（待支付/待确认）可自助取消；已确认及之后须联系客服
  function canCancel(order) {
    return ['unpaid', 'pending'].includes(order.status)
  }

  function orderEditReason(order) {
    if (order.can_edit) return '每天22:00前可修改'
    if (order.status === 'delivering') return '订单配送中，不能修改'
    if (order.status === 'completed') return '订单已完成，不能修改'
    if (order.status === 'cancelled') return '订单已取消，不能修改'
    return '已过22:00，不能修改'
  }

  function addressText(order) {
    return `${order.province || ''}${order.city || ''}${order.district || ''}${order.detail_address || ''}`
  }

  return { paying, cancelling, payOrderNow, cancelOrder, canCancel, orderEditReason, addressText }
}
