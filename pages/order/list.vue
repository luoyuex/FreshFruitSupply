<script setup>
import { computed, ref, shallowRef } from 'vue'
import { onLoad, onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { money, statusLabel } from '../../utils/format.js'
import { request } from '../../utils/request.js'
import { payOrder } from '../../utils/pay.js'
import { hasCustomerLogin, loginWithWeChat } from '../../utils/auth.js'

const tabs = [
  { key: '', label: '全部' },
  { key: 'unpaid', label: '待支付' },
  { key: 'pending', label: '待确认' },
  { key: 'confirmed', label: '已确认' },
  { key: 'delivering', label: '配送中' },
  { key: 'completed', label: '已完成' },
]

const orders = ref([])
const activeStatus = shallowRef('')
const loading = shallowRef(false)
const loginChecked = shallowRef(false)
const paying = shallowRef(false)

const filteredOrders = computed(() => {
  if (!activeStatus.value) return orders.value
  return orders.value.filter((order) => order.status === activeStatus.value)
})

async function ensureLogin() {
  if (hasCustomerLogin()) return true
  loading.value = true
  try {
    await loginWithWeChat()
    return true
  } catch (err) {
    uni.showToast({ title: err.message || '请先登录', icon: 'none' })
    return false
  } finally {
    loading.value = false
  }
}

async function loadOrders() {
  if (!(await ensureLogin())) {
    orders.value = []
    loginChecked.value = true
    return
  }
  loading.value = true
  try {
    orders.value = await request({ url: '/orders/my' })
  } catch (err) {
    uni.showToast({ title: err.message || '订单加载失败', icon: 'none' })
  } finally {
    loading.value = false
    loginChecked.value = true
  }
}

function switchStatus(status) {
  activeStatus.value = status
}

function orderEditReason(order) {
  if (order.can_edit) return '每天22:30前可修改'
  if (order.status === 'delivering') return '订单配送中，不能修改'
  if (order.status === 'completed') return '订单已完成，不能修改'
  if (order.status === 'cancelled') return '订单已取消，不能修改'
  return '已过22:30，不能修改'
}

function editOrder(order) {
  if (!order.can_edit) {
    uni.showToast({ title: orderEditReason(order), icon: 'none' })
    return
  }
  uni.navigateTo({ url: `/pages/order/create?edit=${order.id}` })
}

async function payOrderNow(order) {
  if (paying.value) return
  paying.value = true
  try {
    await payOrder(order.id)
    uni.showToast({ title: '支付成功', icon: 'success' })
    await loadOrders()
  } catch (err) {
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
      try {
        await request({ url: `/orders/${order.id}/cancel`, method: 'POST' })
        uni.showToast({ title: paid ? '已取消，退款处理中' : '订单已取消', icon: 'none' })
        await loadOrders()
      } catch (err) {
        uni.showToast({ title: err.message || '取消失败', icon: 'none' })
      }
    },
  })
}

// 已付款、未进入配送的订单可由用户取消并触发退款
function canCancel(order) {
  return ['unpaid', 'pending', 'confirmed'].includes(order.status)
}

function goBuy() {
  uni.switchTab({ url: '/pages/category/index' })
}

function addressText(order) {
  return `${order.province || ''}${order.city || ''}${order.district || ''}${order.detail_address || ''}`
}

onLoad((query) => {
  activeStatus.value = query?.status || ''
})

onShow(loadOrders)

onPullDownRefresh(async () => {
  try {
    await loadOrders()
  } finally {
    uni.stopPullDownRefresh()
  }
})
</script>

<template>
  <view class="page">
    <scroll-view class="tabs" scroll-x>
      <view class="tab-row">
        <view
          v-for="tab in tabs"
          :key="tab.key || 'all'"
          class="tab"
          :class="{ active: activeStatus === tab.key }"
          @tap="switchStatus(tab.key)"
        >
          {{ tab.label }}
        </view>
      </view>
    </scroll-view>

    <view v-if="loading && !orders.length" class="empty">正在加载订单...</view>
    <view v-else-if="loginChecked && !filteredOrders.length" class="empty">
      <image class="empty-icon" src="/static/icons/file-text.svg" mode="aspectFit" />
      <view>暂无订单</view>
      <button class="go-buy" @tap="goBuy">去选水果</button>
    </view>

    <view v-for="order in filteredOrders" :key="order.id" class="order-card">
      <view class="order-head">
        <text class="order-no">{{ order.order_no }}</text>
        <text class="order-status">{{ statusLabel(order.status) }}</text>
      </view>

      <view class="contact">{{ order.receiver_name }} {{ order.receiver_phone }}</view>
      <view class="address">{{ addressText(order) }}</view>

      <view class="items">
        <view v-for="item in order.items" :key="item.id" class="item-row">
          <text class="item-name">{{ item.fruit_name }} {{ item.spec }}</text>
          <text class="item-qty">x{{ item.quantity }}{{ item.unit }}</text>
          <text class="item-money">¥{{ money(item.subtotal) }}</text>
        </view>
      </view>

      <view class="order-bottom">
        <view>
          <view v-if="order.status === 'unpaid'" class="total">待支付 ¥{{ money(order.payable_total) }}</view>
          <view v-else-if="Number(order.discount_amount) > 0 || Number(order.delivery_fee) > 0" class="total">实付 ¥{{ money(order.payable_total) }}</view>
          <view v-else class="total">预估总价 ¥{{ money(order.estimated_total) }}</view>
          <view v-if="Number(order.discount_amount) > 0" class="saved-line">已优惠 ¥{{ money(order.discount_amount) }} · 原价 ¥{{ money(order.estimated_total) }}</view>
          <view v-if="Number(order.delivery_fee) > 0" class="fee-line">含配送费 ¥{{ money(order.delivery_fee) }}</view>
          <view v-if="order.status === 'unpaid'" class="edit-hint">超时未支付将自动关闭</view>
          <view v-else class="edit-hint">{{ orderEditReason(order) }}</view>
        </view>
        <view class="order-actions">
          <button v-if="canCancel(order)" class="cancel-order" @tap="cancelOrder(order)">取消订单</button>
          <button v-if="order.status === 'unpaid'" class="pay-order" :loading="paying" :disabled="paying" @tap="payOrderNow(order)">去支付</button>
          <button v-else class="edit-order" :class="{ disabled: !order.can_edit }" @tap="editOrder(order)">修改订单</button>
        </view>
      </view>
    </view>
  </view>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding: 20rpx 22rpx 44rpx;
  background: #f3f3f3;
  box-sizing: border-box;
}

.tabs {
  white-space: nowrap;
  margin-bottom: 20rpx;
}

.tab-row {
  display: flex;
  gap: 14rpx;
  padding: 4rpx 2rpx 10rpx;
}

.tab {
  flex: 0 0 auto;
  padding: 14rpx 24rpx;
  border-radius: 999rpx;
  color: #666;
  background: #fff;
  font-size: 26rpx;
  font-weight: 800;
}

.tab.active {
  color: #fff;
  background: #ffb700;
}

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 120rpx;
  text-align: center;
  color: #888;
  font-size: 28rpx;
}

.empty-icon {
  width: 78rpx;
  height: 78rpx;
  margin-bottom: 18rpx;
}

.go-buy {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 210rpx;
  height: 72rpx;
  line-height: 72rpx;
  margin: 28rpx auto 0;
  border-radius: 999rpx;
  color: #fff;
  background: #ffb700;
  font-size: 28rpx;
  font-weight: 900;
}

.go-buy::after,
.edit-order::after {
  border: none;
}

.order-card {
  margin-bottom: 22rpx;
  padding: 26rpx;
  border-radius: 24rpx;
  background: #fff;
}

.order-head,
.item-row,
.order-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.order-no {
  color: #666;
  font-size: 25rpx;
}

.order-status {
  color: #ff5a00;
  font-size: 26rpx;
  font-weight: 900;
}

.contact {
  margin-top: 18rpx;
  color: #333;
  font-size: 30rpx;
  font-weight: 900;
}

.address {
  margin-top: 10rpx;
  color: #666;
  font-size: 26rpx;
  line-height: 1.45;
}

.items {
  margin-top: 20rpx;
  padding: 16rpx 18rpx;
  border-radius: 18rpx;
  background: #f8f8f8;
}

.item-row + .item-row {
  margin-top: 12rpx;
}

.item-name {
  flex: 1;
  min-width: 0;
  color: #444;
  font-size: 25rpx;
}

.item-qty {
  color: #777;
  font-size: 24rpx;
}

.item-money {
  min-width: 120rpx;
  text-align: right;
  color: #333;
  font-size: 25rpx;
  font-weight: 800;
}

.order-bottom {
  margin-top: 22rpx;
}

.total {
  color: #f20d2f;
  font-size: 30rpx;
  font-weight: 900;
}

.edit-hint {
  margin-top: 8rpx;
  color: #999;
  font-size: 23rpx;
}

.saved-line {
  margin-top: 6rpx;
  color: #ff6a00;
  font-size: 23rpx;
}

.fee-line {
  margin-top: 6rpx;
  color: #999;
  font-size: 23rpx;
}

.edit-order {
  width: 168rpx;
  height: 62rpx;
  line-height: 62rpx;
  border-radius: 999rpx;
  color: #fff;
  background: #ffb700;
  font-size: 24rpx;
  font-weight: 900;
}

.edit-order.disabled {
  color: #999;
  background: #eee;
}

.order-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12rpx;
}

.cancel-order {
  width: 168rpx;
  height: 62rpx;
  line-height: 62rpx;
  border-radius: 999rpx;
  color: #666;
  background: #f1f2f4;
  font-size: 24rpx;
  font-weight: 900;
}

.pay-order {
  width: 168rpx;
  height: 62rpx;
  line-height: 62rpx;
  border-radius: 999rpx;
  color: #fff;
  background: #f20d2f;
  font-size: 24rpx;
  font-weight: 900;
}

.cancel-order::after,
.pay-order::after {
  border: none;
}
</style>
