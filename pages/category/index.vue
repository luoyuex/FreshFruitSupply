<script setup>
import { computed, onMounted, shallowRef } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { useFruitQuotes } from '../../composables/useFruitQuotes.js'
import { addCartItem, cartCount } from '../../utils/cart.js'
import { fruitIcon, money, statusLabel } from '../../utils/format.js'
import { request } from '../../utils/request.js'
import { hasCustomerLogin } from '../../utils/auth.js'

const { loading, error, keyword, activeCategory, categoryItems, categories, visibleFruits, loadFruits } = useFruitQuotes()
const customer = shallowRef(null)
const cartTotal = shallowRef(0)

// 拖动相关状态
const cartX = shallowRef(0)
const cartY = shallowRef(0)
const isDragging = shallowRef(false)
const startX = shallowRef(0)
const startY = shallowRef(0)
const moveStartX = shallowRef(0)
const moveStartY = shallowRef(0)
const hasMoved = shallowRef(false)

const sideCategories = computed(() => [{ name: '全部', id: 'all' }, ...categoryItems.value])
const isVerified = computed(() => customer.value?.verification_status === 'verified')

function displayVerifiedPrice(price) {
  return isVerified.value ? `¥${money(price)}` : '???'
}

async function loadCustomer() {
  if (!hasCustomerLogin()) {
    customer.value = null
    return
  }
  try {
    customer.value = await request({ url: '/customers/me' })
  } catch (err) {
    customer.value = null
  }
}

function setCategory(category) {
  activeCategory.value = category
  uni.setStorageSync('active_category', category)
}

function primaryImage(fruit) {
  return fruit.image_urls?.[0] || fruit.image_url || ''
}

function productDesc(fruit) {
  return [fruit.origin, fruit.quote?.grade].filter(Boolean).join(' · ')
}

function goDetail(fruit) {
  uni.navigateTo({ url: `/pages/product/detail?id=${fruit.id}` })
}

function addToCart(fruit) {
  addCartItem(fruit, Number(fruit.quote?.min_order_quantity || 1))
  cartTotal.value = cartCount()
  uni.showToast({ title: '已加入预订车', icon: 'success' })
}

function goCart() {
  uni.switchTab({ url: '/pages/cart/index' })
}

function initCartPosition() {
  const sysInfo = uni.getSystemInfoSync()
  const cartSize = 90 / 750 * sysInfo.windowWidth
  cartX.value = sysInfo.windowWidth - cartSize - 26
  cartY.value = sysInfo.windowHeight - 128 - cartSize
}

function onCartTouchStart(e) {
  const touch = e.touches[0]
  startX.value = touch.clientX
  startY.value = touch.clientY
  moveStartX.value = cartX.value
  moveStartY.value = cartY.value
  isDragging.value = true
  hasMoved.value = false
}

function onCartTouchMove(e) {
  if (!isDragging.value) return
  const touch = e.touches[0]
  const dx = touch.clientX - startX.value
  const dy = touch.clientY - startY.value

  if (Math.abs(dx) > 5 || Math.abs(dy) > 5) {
    hasMoved.value = true
  }

  const sysInfo = uni.getSystemInfoSync()
  const cartSize = 90 / 750 * sysInfo.windowWidth
  let newX = moveStartX.value + dx
  let newY = moveStartY.value + dy

  // 边界限制
  newX = Math.max(0, Math.min(newX, sysInfo.windowWidth - cartSize))
  newY = Math.max(0, Math.min(newY, sysInfo.windowHeight - cartSize))

  cartX.value = newX
  cartY.value = newY
}

function onCartTouchEnd() {
  isDragging.value = false
}

function onCartTap() {
  if (hasMoved.value) return
  goCart()
}

onMounted(() => {
  initCartPosition()
  loadFruits()
  loadCustomer()
})

onShow(() => {
  const storedCategory = uni.getStorageSync('active_category')
  if (storedCategory) activeCategory.value = storedCategory
  cartTotal.value = cartCount()
  loadCustomer()
})

onPullDownRefresh(async () => {
  try {
    await Promise.all([loadFruits(), loadCustomer()])
    cartTotal.value = cartCount()
  } finally {
    uni.stopPullDownRefresh()
  }
})

function onShareAppMessage() {
  return {
    title: '珍果链 - 水果分类',
    path: '/pages/category/index',
    imageUrl: ''
  }
}

function onShareTimeline() {
  return {
    title: '珍果链 - 水果分类',
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

    <view class="search-wrap">
      <text class="search-icon">⌕</text>
      <input v-model="keyword" class="search-input" placeholder="搜索商品" />
    </view>

    <view v-if="!sideCategories.length && !loading" class="empty-card">
      <view class="empty-icon">🍎</view>
      <view class="empty-title">还没有可用分类</view>
      <view class="empty-desc">请先到后台报价管理添加分类和水果报价。</view>
    </view>

    <view v-else class="content-card">
      <scroll-view scroll-y class="side-menu">
        <view
          v-for="category in sideCategories"
          :key="category.id"
          class="side-item"
          :class="{ active: activeCategory === category.name }"
          @tap="setCategory(category.name)"
        >
          {{ category.name }}
        </view>
      </scroll-view>

      <view class="goods-panel">
        <view v-if="error" class="notice">后端连接失败，请确认 Python 服务和数据库已启动</view>
        <view v-if="loading" class="notice">加载商品中...</view>

        <scroll-view scroll-y class="goods-scroll">
          <view v-for="fruit in visibleFruits" :key="fruit.id" class="goods-row" @tap="goDetail(fruit)">
            <view class="goods-img">
              <image v-if="primaryImage(fruit)" class="goods-image" :src="primaryImage(fruit)" mode="aspectFill" />
              <text v-else>{{ fruitIcon(fruit.name) }}</text>
              <view v-if="fruit.stock_status === 'out_of_stock'" class="sold-out-mask">
                <text class="sold-out-text">售罄</text>
              </view>
            </view>
            <view class="goods-info">
              <view class="goods-name">{{ fruit.name }} {{ fruit.spec }}</view>
              <view v-if="productDesc(fruit)" class="goods-desc">{{ productDesc(fruit) }}</view>
              <view class="goods-status">{{ statusLabel(fruit.stock_status) }} · 起订 {{ fruit.quote?.min_order_quantity }}{{ fruit.unit }}</view>
              <view class="price-line">
                <text class="goods-price">¥{{ money(fruit.quote?.normal_price) }}</text>
                <text class="verified-price">认证价 {{ displayVerifiedPrice(fruit.quote?.verified_price) }}</text>
              </view>
            </view>
            <view class="add" @tap.stop="addToCart(fruit)"><view class="add-line horizontal"></view><view class="add-line vertical"></view></view>
          </view>
        </scroll-view>
      </view>
    </view>

    <view
      v-if="cartTotal"
      class="float-cart"
      :style="{ left: cartX + 'px', top: cartY + 'px' }"
      @touchstart.stop.prevent="onCartTouchStart"
      @touchmove.stop.prevent="onCartTouchMove"
      @touchend.stop.prevent="onCartTouchEnd"
      @tap.stop="onCartTap"
    >
      <text>🛒</text>
      <text class="cart-badge">{{ cartTotal }}</text>
    </view>
  </view>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f3f3f3;
}



.search-wrap {
  display: flex;
  align-items: center;
  height: 80rpx;
  margin: 24rpx 26rpx 18rpx;
  padding: 0 28rpx;
  border-radius: 999rpx;
  background: #fff;
}

.search-icon { margin-right: 14rpx; color: #aaa; font-size: 40rpx; }
.search-input { flex: 1; height: 80rpx; color: #222; font-size: 30rpx; }

.empty-card {
  margin: 26rpx;
  padding: 90rpx 34rpx;
  border-radius: 26rpx;
  text-align: center;
  background: #fff;
}

.empty-icon { font-size: 78rpx; }
.empty-title { margin-top: 18rpx; color: #173b16; font-size: 32rpx; font-weight: 900; }
.empty-desc { margin-top: 12rpx; color: #768273; font-size: 26rpx; line-height: 1.5; }

.content-card {
  display: flex;
  flex: 1;
  min-height: 0;
  background: #fff;
}

.side-menu {
  width: 172rpx;
  height: 100%;
  overflow-y: auto;
  background: #fff;
}

.side-item {
  display: flex;
  align-items: center;
  gap: 8rpx;
  position: relative;
  padding: 28rpx 10rpx 28rpx 20rpx;
  color: #333;
  font-size: 27rpx;
  line-height: 1.35;
}

.side-item.active {
  color: #ffb000;
  font-weight: 800;
}

.side-item.active::before {
  position: absolute;
  left: 0;
  top: 28rpx;
  width: 6rpx;
  height: 42rpx;
  background: #ffb700;
  content: '';
}

.goods-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  border-left: 1rpx solid #f0f0f0;
}



.notice {
  margin: 0 20rpx 14rpx;
  padding: 14rpx 18rpx;
  border-radius: 16rpx;
  color: #ff6a00;
  background: #fff5e6;
  font-size: 23rpx;
}

.goods-scroll {
  flex: 1;
  min-height: 0;
}

.goods-row {
  position: relative;
  display: flex;
  gap: 22rpx;
  padding: 24rpx 28rpx 24rpx 20rpx;
  border-bottom: 1rpx solid #eeeeee;
}

.goods-img {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 170rpx;
  height: 170rpx;
  overflow: hidden;
  border-radius: 20rpx;
  font-size: 98rpx;
  background: #fafafa;
}

.goods-image {
  width: 100%;
  height: 100%;
}

.goods-info {
  flex: 1;
  min-width: 0;
  padding-right: 54rpx;
}

.goods-name {
  color: #292929;
  font-size: 31rpx;
  font-weight: 800;
  line-height: 1.45;
}

.goods-desc,
.goods-status {
  margin-top: 8rpx;
  color: #999;
  font-size: 24rpx;
}

.price-line {
  display: flex;
  flex-direction: column;
  margin-top: 18rpx;
}

.goods-price {
  color: #f20d2f;
  font-size: 38rpx;
  font-weight: 900;
}

.verified-price {
  margin-top: 4rpx;
  color: #ff8a00;
  font-size: 23rpx;
  font-weight: 700;
}

.add {
  position: absolute;
  right: 28rpx;
  bottom: 38rpx;
  width: 58rpx;
  height: 58rpx;
  border-radius: 18rpx;
  background: #ffb700;
}

.add-line {
  position: absolute;
  left: 50%;
  top: 50%;
  border-radius: 999rpx;
  background: #fff;
  transform: translate(-50%, -50%);
}

.add-line.horizontal {
  width: 28rpx;
  height: 6rpx;
}

.add-line.vertical {
  width: 6rpx;
  height: 28rpx;
}

.sold-out-mask {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 20rpx;
}

.sold-out-text {
  color: #fff;
  font-size: 28rpx;
  font-weight: 900;
  letter-spacing: 4rpx;
}

.float-cart {
  position: fixed;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 90rpx;
  height: 90rpx;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 8rpx 24rpx rgba(0,0,0,.14);
  font-size: 40rpx;
  z-index: 999;
}

.cart-badge {
  position: absolute;
  top: 0;
  right: 0;
  min-width: 30rpx;
  height: 30rpx;
  line-height: 30rpx;
  border-radius: 999rpx;
  text-align: center;
  color: #fff;
  background: #f20d2f;
  font-size: 20rpx;
}
</style>
