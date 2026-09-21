<script setup>
import { ref, shallowRef } from 'vue'
import { onLoad, onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { money, statusLabel, shortDateTime } from '../../utils/format.js'
import { request } from '../../utils/request.js'
import { hasCustomerLogin, loginWithWeChat } from '../../utils/auth.js'
import { createOrderActions } from '../../utils/order-actions.js'

// 订单详情页：支持两种入口参数
// 1. id            —— 站内跳转（订单列表点击卡片）
// 2. out_trade_no  —— 微信支付「订单路径」跳转（pages/order/detail?out_trade_no=${商品订单号}）

const order = ref(null)
const orderId = shallowRef(null)
const loading = shallowRef(false)
const loadFailed = shallowRef(false)
const loginChecked = shallowRef(false)

const { paying, payOrderNow, cancelOrder, canCancel, orderEditReason, addressText } =
  createOrderActions({ onChanged: loadOrder })

async function ensureLogin() {
  if (hasCustomerLogin()) return true
  try {
    await loginWithWeChat()
    return true
  } catch (err) {
    uni.showToast({ title: err.message || '请先登录', icon: 'none' })
    return false
  } finally {
    loginChecked.value = true
  }
}

async function loadOrder() {
  if (!orderId.value) return
  if (!(await ensureLogin())) {
    order.value = null
    return
  }
  loading.value = true
  try {
    order.value = await request({ url: `/orders/detail/${orderId.value}` })
    loadFailed.value = false
  } catch (err) {
    loadFailed.value = true
    uni.showToast({ title: err.message || '订单加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

// 微信支付订单路径入口：out_trade_no 换成订单 id 后走统一加载
async function loadByOutTradeNo(outTradeNo) {
  if (!(await ensureLogin())) return
  loading.value = true
  try {
    order.value = await request({ url: `/orders/detail/out-trade-no/${outTradeNo}` })
    orderId.value = order.value.id
    loadFailed.value = false
  } catch (err) {
    loadFailed.value = true
    uni.showToast({ title: err.message || '订单加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function goOrders() {
  uni.redirectTo({ url: '/pages/order/list' })
}

onLoad((query) => {
  if (query?.id) {
    orderId.value = Number(query.id)
  } else if (query?.out_trade_no) {
    loadByOutTradeNo(query.out_trade_no)
  }
})

onShow(() => {
  if (orderId.value) loadOrder()
})

onPullDownRefresh(async () => {
  try {
    if (orderId.value) await loadOrder()
  } finally {
    uni.stopPullDownRefresh()
  }
})
</script>

<template>
  <view class="page">
    <view v-if="loading && !order" class="empty">正在加载订单...</view>
    <view v-else-if="!order" class="empty">
      <image class="empty-icon" src="/static/icons/file-text.svg" mode="aspectFit" />
      <view>{{ loadFailed ? '订单加载失败或不存在' : '订单不存在' }}</view>
      <button class="go-orders" @tap="goOrders">查看我的订单</button>
    </view>

    <template v-else>
      <!-- 状态卡 -->
      <view class="card status-card">
        <view class="status-line">
          <text class="status-label">{{ statusLabel(order.status) }}</text>
          <text v-if="order.status === 'unpaid'" class="status-hint">超时未支付将自动关闭</text>
        </view>
        <view class="meta-line">
          <text class="meta-label">订单编号</text>
          <text class="meta-value">{{ order.order_no }}</text>
        </view>
        <view class="meta-line">
          <text class="meta-label">下单时间</text>
          <text class="meta-value">{{ shortDateTime(order.created_at) }}</text>
        </view>
      </view>

      <!-- 收货信息 -->
      <view class="card">
        <view class="section-title">收货信息</view>
        <view class="contact">{{ order.receiver_name }} {{ order.receiver_phone }}</view>
        <view class="address">{{ addressText(order) }}</view>
        <view v-if="order.delivery_note" class="note">备注：{{ order.delivery_note }}</view>
      </view>

      <!-- 商品明细 -->
      <view class="card">
        <view class="section-title">商品明细</view>
        <view v-for="item in order.items" :key="item.id" class="item-row">
          <image
            v-if="item.image_url"
            class="item-img"
            :src="item.image_url"
            mode="aspectFill"
          />
          <view v-else class="item-img item-img-placeholder" />
          <view class="item-main">
            <view class="item-name">{{ item.fruit_name }}</view>
            <view class="item-qty">x{{ item.quantity }}{{ item.unit }}</view>
          </view>
          <text class="item-money">¥{{ money(item.subtotal) }}</text>
        </view>
        <view v-if="order.reissue_coupons && order.reissue_coupons.length" class="reissue">
          <view v-for="coupon in order.reissue_coupons" :key="coupon.id" class="reissue-row">
            🎁 {{ coupon.name }}
          </view>
        </view>
      </view>

      <!-- 费用明细 -->
      <view class="card">
        <view class="section-title">费用明细</view>
        <view class="fee-row">
          <text class="fee-label">商品总价</text>
          <text class="fee-value">¥{{ money(order.estimated_total) }}</text>
        </view>
        <view v-if="Number(order.discount_amount) > 0" class="fee-row">
          <text class="fee-label discount">优惠</text>
          <text class="fee-value discount">-¥{{ money(order.discount_amount) }}</text>
        </view>
        <view v-if="Number(order.delivery_fee) > 0" class="fee-row">
          <text class="fee-label">配送费</text>
          <text class="fee-value">¥{{ money(order.delivery_fee) }}</text>
        </view>
        <view v-if="order.status !== 'unpaid' && Number(order.paid_amount) > 0" class="fee-row">
          <text class="fee-label">已支付</text>
          <text class="fee-value">¥{{ money(order.paid_amount) }}</text>
        </view>
        <view class="fee-row total-row">
          <text class="fee-label">应付总额</text>
          <text class="fee-value total">¥{{ money(order.payable_total || order.estimated_total) }}</text>
        </view>
      </view>

      <!-- 底部操作 -->
      <view v-if="canCancel(order) || order.status === 'unpaid'" class="actions">
        <button
          v-if="canCancel(order)"
          class="cancel-order"
          @tap.stop="cancelOrder(order)"
        >取消订单</button>
        <button
          v-if="order.status === 'unpaid'"
          class="pay-order"
          :loading="paying"
          :disabled="paying"
          @tap.stop="payOrderNow(order)"
        >去支付</button>
      </view>
      <view v-else class="edit-hint">{{ orderEditReason(order) }}</view>
    </template>
  </view>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding: 20rpx 22rpx 44rpx;
  background: #f3f3f3;
  box-sizing: border-box;
}

.card {
  margin-bottom: 22rpx;
  padding: 26rpx;
  border-radius: 24rpx;
  background: #fff;
}

.status-card {
  background: #fff;
}

.status-line {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16rpx;
}

.status-label {
  color: #ff5a00;
  font-size: 34rpx;
  font-weight: 900;
}

.status-hint {
  color: #999;
  font-size: 23rpx;
}

.meta-line {
  display: flex;
  justify-content: space-between;
  gap: 16rpx;
  margin-top: 14rpx;
}

.meta-label {
  color: #999;
  font-size: 25rpx;
}

.meta-value {
  color: #333;
  font-size: 25rpx;
}

.section-title {
  margin-bottom: 18rpx;
  color: #333;
  font-size: 28rpx;
  font-weight: 900;
}

.contact {
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

.note {
  margin-top: 10rpx;
  color: #999;
  font-size: 24rpx;
}

.item-row {
  display: flex;
  align-items: center;
  gap: 18rpx;
  padding: 12rpx 0;
}

.item-row + .item-row {
  border-top: 1rpx solid #f5f5f5;
}

.item-img {
  flex: 0 0 auto;
  width: 96rpx;
  height: 96rpx;
  border-radius: 14rpx;
  background: #f8f8f8;
}

.item-main {
  flex: 1;
  min-width: 0;
}

.item-name {
  color: #444;
  font-size: 26rpx;
}

.item-qty {
  margin-top: 8rpx;
  color: #777;
  font-size: 24rpx;
}

.item-money {
  min-width: 120rpx;
  text-align: right;
  color: #333;
  font-size: 26rpx;
  font-weight: 800;
}

.reissue {
  margin-top: 14rpx;
  padding: 14rpx 18rpx;
  border-radius: 14rpx;
  background: #fff8e6;
}

.reissue-row {
  color: #b8860b;
  font-size: 24rpx;
}

.reissue-row + .reissue-row {
  margin-top: 8rpx;
}

.fee-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  padding: 10rpx 0;
}

.fee-label,
.fee-value {
  color: #666;
  font-size: 26rpx;
}

.fee-value {
  color: #333;
}

.discount {
  color: #ff6a00;
}

.total-row {
  margin-top: 8rpx;
  padding-top: 18rpx;
  border-top: 1rpx solid #f0f0f0;
}

.total {
  color: #f20d2f;
  font-size: 32rpx;
  font-weight: 900;
}

.actions {
  position: fixed;
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
  justify-content: flex-end;
  gap: 18rpx;
  padding: 20rpx 22rpx calc(20rpx + env(safe-area-inset-bottom));
  background: #fff;
  box-shadow: 0 -4rpx 16rpx rgba(0, 0, 0, 0.04);
}

.edit-hint {
  padding: 8rpx 6rpx;
  color: #999;
  font-size: 24rpx;
  text-align: center;
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

.go-orders {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 240rpx;
  height: 72rpx;
  line-height: 72rpx;
  margin: 28rpx auto 0;
  border-radius: 999rpx;
  color: #fff;
  background: #ffb700;
  font-size: 28rpx;
  font-weight: 900;
}

.go-orders::after,
.cancel-order::after,
.pay-order::after {
  border: none;
}

.cancel-order {
  width: 200rpx;
  height: 72rpx;
  line-height: 72rpx;
  border-radius: 999rpx;
  color: #666;
  background: #f1f2f4;
  font-size: 26rpx;
  font-weight: 900;
}

.pay-order {
  width: 200rpx;
  height: 72rpx;
  line-height: 72rpx;
  border-radius: 999rpx;
  color: #fff;
  background: #f20d2f;
  font-size: 26rpx;
  font-weight: 900;
}
</style>
