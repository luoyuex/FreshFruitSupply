<script setup>
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { computed, ref, shallowRef } from 'vue'
import { clearSelectedCartItems, getCartItems, removeCartItem, updateCartItem } from '../../utils/cart.js'
import { money, statusLabel } from '../../utils/format.js'
import { request } from '../../utils/request.js'

const items = ref([])
const verified = shallowRef(false)
const loading = shallowRef(false)
const managing = shallowRef(false)

const selectedItems = computed(() => items.value.filter((item) => item.selected))
const allSelected = computed(() => items.value.length > 0 && selectedItems.value.length === items.value.length)
const total = computed(() => selectedItems.value.reduce((sum, item) => {
  const price = Number(verified.value ? item.verified_price : item.normal_price)
  return sum + price * Number(item.quantity || 0)
}, 0))

async function loadCart() {
  managing.value = false
  items.value = getCartItems()

  // 获取最新商品状态
  if (items.value.length > 0) {
    loading.value = true
    try {
      const fruits = await request({ url: '/fruits' })
      const fruitMap = new Map(fruits.map((f) => [f.id, f]))

      let changed = false
      items.value = items.value.map((item) => {
        const latest = fruitMap.get(item.id)
        if (latest) {
          const updates = {}
          if (latest.stock_status !== item.stock_status) {
            updates.stock_status = latest.stock_status
            changed = true
          }
          if (latest.quote?.normal_price !== item.normal_price) {
            updates.normal_price = latest.quote?.normal_price || 0
            changed = true
          }
          if (latest.quote?.verified_price !== item.verified_price) {
            updates.verified_price = latest.quote?.verified_price || 0
            changed = true
          }
          if (Object.keys(updates).length > 0) {
            updateCartItem(item.id, updates)
            return { ...item, ...updates }
          }
        }
        return item
      })

      if (changed) {
        items.value = getCartItems()
      }
    } catch (err) {
      // 静默失败，使用本地数据
    } finally {
      loading.value = false
    }
  }

  verified.value = uni.getStorageSync('verification_status') === 'verified'
}

function itemImage(item) {
  return item.image_url || item.image_urls?.[0] || ''
}

function itemInitial(name = '') {
  return String(name).trim().slice(0, 1) || '果'
}

function toggleItem(item) {
  item.selected = !item.selected
  updateCartItem(item.id, { selected: item.selected })
}

function toggleAll() {
  const checked = !allSelected.value
  items.value = items.value.map((item) => ({ ...item, selected: checked }))
  items.value.forEach((item) => updateCartItem(item.id, { selected: checked }))
}

function changeQuantity(item, delta) {
  const min = Number(item.min_order_quantity || 1)
  const next = Math.max(min, Number(item.quantity || min) + delta)
  item.quantity = next
  updateCartItem(item.id, { quantity: next })
}

function deleteItem(item) {
  uni.showModal({
    title: '移除商品',
    content: `确认从预订车移除 ${item.name}？`,
    success: (res) => {
      if (res.confirm) {
        items.value = removeCartItem(item.id)
      }
    },
  })
}

function toggleManage() {
  managing.value = !managing.value
}

// 编辑态批量删除已勾选商品
function deleteSelected() {
  if (!selectedItems.value.length) {
    uni.showToast({ title: '请选择商品', icon: 'none' })
    return
  }
  uni.showModal({
    title: '移除商品',
    content: `确认从预订车移除选中的 ${selectedItems.value.length} 件商品？`,
    success: (res) => {
      if (!res.confirm) return
      selectedItems.value.forEach((item) => removeCartItem(item.id))
      items.value = getCartItems()
      if (!items.value.length) managing.value = false
    },
  })
}

function goVerify() {
  uni.navigateTo({ url: '/pages/verify/index' })
}

function goCategory() {
  uni.switchTab({ url: '/pages/category/index' })
}

function checkout() {
  if (!selectedItems.value.length) {
    uni.showToast({ title: '请选择商品', icon: 'none' })
    return
  }
  uni.setStorageSync('checkout_items', JSON.stringify(selectedItems.value))
  uni.navigateTo({ url: '/pages/order/create?cart=1' })
}

onShow(loadCart)

onPullDownRefresh(() => {
  loadCart()
  uni.stopPullDownRefresh()
})

function onShareAppMessage() {
  return {
    title: '珍果链 - 购物车',
    path: '/pages/cart/index',
    imageUrl: ''
  }
}

function onShareTimeline() {
  return {
    title: '珍果链 - 购物车',
    query: '',
    imageUrl: ''
  }
}

defineExpose({
  onShareAppMessage,
  onShareTimeline
})
</script>

<template>
  <view class="page">

    <view class="cart-title-row">
      <view></view>
      <view class="cart-title">购物车({{ items.length }})</view>
      <view v-if="items.length" class="manage" @tap="toggleManage">{{ managing ? '完成' : '管理' }}</view>
      <view v-else></view>
    </view>

    <view v-if="!verified" class="auth-strip">
      <text>认证店铺信息可享超低价及新人礼包</text>
      <button class="auth-btn" @tap="goVerify">去认证</button>
    </view>

    <view v-if="items.length === 0" class="empty">
      <view class="empty-icon">🛒</view>
      <view class="empty-title">预订车还是空的</view>
      <button class="go" @tap="goCategory">去选水果</button>
    </view>

    <view v-for="item in items" :key="item.id" class="cart-card">
      <view class="package-row">
        <view class="circle" :class="{ checked: item.selected }" @tap="toggleItem(item)"></view>
        <text class="package-title">包裹</text>
      </view>
      <view class="goods-row">
        <view class="circle small" :class="{ checked: item.selected }" @tap="toggleItem(item)"></view>
        <view class="goods-img">
          <image v-if="itemImage(item)" class="goods-photo" :src="itemImage(item)" mode="aspectFill" />
          <text v-else>{{ itemInitial(item.name) }}</text>
        </view>
        <view class="goods-info">
          <view class="goods-name">{{ item.name }}</view>
          <view class="goods-spec">{{ item.spec }}</view>
          <view class="goods-price">¥{{ money((verified ? item.verified_price : item.normal_price) * item.quantity) }}</view>
          <view class="stock">{{ statusLabel(item.stock_status) }}</view>
        </view>
        <view class="stepper">
          <button class="step" @tap="changeQuantity(item, -1)">−</button>
          <text class="quantity">{{ item.quantity }}</text>
          <button class="step" @tap="changeQuantity(item, 1)">＋</button>
        </view>
      </view>
      <view class="delete" @tap="deleteItem(item)">移除</view>
    </view>

    <view class="bottom-bar">
      <view class="select-all" @tap="toggleAll">
        <view class="circle" :class="{ checked: allSelected }"></view>
        <text>全选</text>
      </view>
      <view v-if="managing" class="settle-area">
        <button class="delete-selected" :class="{ active: selectedItems.length }" @tap="deleteSelected">删除选中{{ selectedItems.length ? `(${selectedItems.length})` : '' }}</button>
      </view>
      <view v-else class="settle-area">
        <text class="sum-label">合计</text>
        <text class="sum-price">¥{{ money(total) }}</text>
        <button class="settle" :class="{ active: selectedItems.length }" @tap="checkout">去预订</button>
      </view>
    </view>
  </view>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding-bottom: 188rpx;
  background: #f3f3f3;
}



.cart-title-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  align-items: center;
  height: 106rpx;
  padding: 0 28rpx;
  background: #fff;
}

.cart-title {
  text-align: center;
  color: #111;
  font-size: 36rpx;
  font-weight: 700;
}

.manage {
  text-align: right;
  color: #111;
  font-size: 28rpx;
}

.manage.active {
  color: #ffb700;
  font-weight: 800;
}

.auth-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 98rpx;
  padding: 0 36rpx;
  color: #ff5a00;
  background: #fff2df;
  font-size: 28rpx;
}

.auth-btn {
  width: 180rpx;
  height: 54rpx;
  line-height: 52rpx;
  border: 2rpx solid #ff5a00;
  border-radius: 999rpx;
  color: #ff5a00;
  background: transparent;
  font-size: 26rpx;
}

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 34rpx 26rpx;
  padding: 70rpx 20rpx;
  border-radius: 24rpx;
  text-align: center;
  background: #fff;
}

.empty-icon { font-size: 82rpx; }
.empty-title { margin-top: 14rpx; color: #666; font-size: 28rpx; }
.go { width: 220rpx; height: 72rpx; line-height: 72rpx; margin: 28rpx auto 0; border-radius: 999rpx; color: #fff; background: #ffb700; font-size: 28rpx; }

.cart-card {
  position: relative;
  margin: 26rpx;
  padding: 30rpx 26rpx 28rpx;
  border-radius: 22rpx;
  background: #fff;
}

.package-row {
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.package-title {
  color: #333;
  font-size: 30rpx;
  font-weight: 800;
}

.circle {
  width: 34rpx;
  height: 34rpx;
  border: 3rpx solid #c4d0de;
  border-radius: 50%;
  box-sizing: border-box;
}

.circle.checked {
  border-color: #ffb700;
  background: radial-gradient(circle at center, #ffb700 0 42%, transparent 45%);
}

.circle.small {
  flex-shrink: 0;
}

.goods-row {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin-top: 48rpx;
}

.goods-img {
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  width: 150rpx;
  height: 120rpx;
  border-radius: 18rpx;
  color: #8a5a00;
  font-size: 42rpx;
  font-weight: 900;
  background: #fafafa;
}

.goods-photo {
  width: 100%;
  height: 100%;
}

.goods-info {
  flex: 1;
  min-width: 0;
}

.goods-name {
  color: #222;
  font-size: 32rpx;
  font-weight: 800;
}

.goods-spec {
  margin-top: 12rpx;
  color: #333;
  font-size: 26rpx;
}

.goods-price {
  margin-top: 20rpx;
  color: #f20d2f;
  font-size: 38rpx;
  font-weight: 900;
}

.stock {
  color: #999;
  font-size: 24rpx;
}

.stepper {
  display: flex;
  align-items: center;
  height: 52rpx;
  overflow: hidden;
  border-radius: 10rpx;
  background: #f1f2f4;
}

.step {
  width: 52rpx;
  height: 52rpx;
  line-height: 48rpx;
  color: #333;
  background: transparent;
  font-size: 36rpx;
}

.quantity {
  min-width: 50rpx;
  text-align: center;
  color: #222;
  font-size: 28rpx;
}

.delete {
  margin-top: 18rpx;
  text-align: right;
  color: #999;
  font-size: 24rpx;
}

.bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: var(--window-bottom);
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 116rpx;
  padding: 0 26rpx;
  border-top: 1rpx solid #eee;
  background: #fff;
  box-sizing: border-box;
}

.select-all,
.settle-area {
  display: flex;
  align-items: center;
  gap: 12rpx;
  color: #333;
  font-size: 28rpx;
}

.sum-label {
  color: #333;
}

.sum-price {
  color: #f20d2f;
  font-size: 42rpx;
  font-weight: 900;
}

.settle {
  width: 170rpx;
  height: 70rpx;
  line-height: 70rpx;
  border-radius: 999rpx;
  color: #fff;
  background: #ffd19a;
  font-size: 30rpx;
  font-weight: 800;
}

.settle.active {
  background: #ffb700;
}

.delete-selected {
  width: 220rpx;
  height: 70rpx;
  line-height: 70rpx;
  border-radius: 999rpx;
  color: #fff;
  background: #f20d2f;
  font-size: 30rpx;
  font-weight: 800;
}

.delete-selected::after { border: none; }
</style>
