<script setup>
import { computed, getCurrentInstance, nextTick, onMounted, shallowRef, watch } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { useFruitQuotes } from '../../composables/useFruitQuotes.js'
import { addCartItem, cartCount } from '../../utils/cart.js'
import { fruitIcon, money, statusLabel } from '../../utils/format.js'
import { request } from '../../utils/request.js'
import { hasCustomerLogin } from '../../utils/auth.js'

const { loading, error, keyword, activeCategory, categoryItems, categories, visibleFruits, loadFruits } = useFruitQuotes()
const customer = shallowRef(null)
const cartTotal = shallowRef(0)

const sideCategories = computed(() => [{ name: '全部', id: 'all' }, ...categoryItems.value])
const isVerified = computed(() => customer.value?.verification_status === 'verified')

const instance = getCurrentInstance()
const scrollAnchor = shallowRef('')
const reachedLower = shallowRef(false)
const nextCategoryReady = shallowRef(false)
let overscrollBaseY = null
let lastScrollTop = 0
const OVERSCROLL_TRIGGER = 55

const nextCategory = computed(() => {
  const list = sideCategories.value
  const index = list.findIndex((item) => item.name === activeCategory.value)
  if (index === -1 || index >= list.length - 1) return null
  return list[index + 1]
})

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
  resetToTop()
}

function resetToTop() {
  reachedLower.value = false
  nextCategoryReady.value = false
  lastScrollTop = 0
  scrollAnchor.value = ''
  nextTick(() => {
    scrollAnchor.value = 'goods-top'
    setTimeout(() => { scrollAnchor.value = '' }, 120)
  })
}

// 测量右侧列表内容是否已撑满可视区域：内容不足一屏时视为“已到底”，
// 这样短列表也能通过上滑切换到下一分类。
function measureAtBottom() {
  if (!instance) return
  nextTick(() => {
    uni.createSelectorQuery()
      .in(instance.proxy)
      .select('.goods-scroll').boundingClientRect()
      .select('.goods-inner').boundingClientRect()
      .exec((res) => {
        const view = res && res[0]
        const inner = res && res[1]
        if (view && inner && inner.height) {
          reachedLower.value = inner.height <= view.height + 2
        }
      })
  })
}

// 搜索状态下列表不按分类过滤，且必须存在下一个分类、当前已滑到底部才允许切换。
function canSwitchNext() {
  return !keyword.value.trim() && !!nextCategory.value && reachedLower.value
}

function onGoodsScroll(event) {
  const top = event.detail.scrollTop
  if (top < lastScrollTop - 8) reachedLower.value = false
  lastScrollTop = top
}

function onScrollLower() {
  reachedLower.value = true
}

function onGoodsTouchStart() {
  overscrollBaseY = null
}

function onGoodsTouchMove(event) {
  const point = event.touches && event.touches[0]
  if (!point) return
  if (!canSwitchNext()) {
    overscrollBaseY = null
    if (nextCategoryReady.value) nextCategoryReady.value = false
    return
  }
  // 到底后开始计量“越界”上滑距离（从到底那一刻的手指位置算起，避免把正常滚动距离算进来）。
  if (overscrollBaseY === null) {
    overscrollBaseY = point.clientY
    return
  }
  const distance = overscrollBaseY - point.clientY
  const ready = distance >= OVERSCROLL_TRIGGER
  if (ready !== nextCategoryReady.value) nextCategoryReady.value = ready
}

function onGoodsTouchEnd() {
  if (nextCategoryReady.value && canSwitchNext()) {
    setCategory(nextCategory.value.name)
  }
  nextCategoryReady.value = false
  overscrollBaseY = null
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

onMounted(() => {
  loadFruits()
  loadCustomer()
})

watch(() => visibleFruits.value.length, () => {
  measureAtBottom()
})

onShow(() => {
  const storedCategory = uni.getStorageSync('active_category')
  if (storedCategory) activeCategory.value = storedCategory
  cartTotal.value = cartCount()
  loadCustomer()
  measureAtBottom()
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

        <!-- 骨架屏 -->
        <view v-if="loading" class="goods-scroll">
          <view v-for="i in 5" :key="i" class="goods-row">
            <view class="goods-img skeleton"></view>
            <view class="goods-info">
              <view class="goods-name skeleton"></view>
              <view class="goods-desc skeleton"></view>
              <view class="goods-status skeleton"></view>
              <view class="price-line">
                <view class="goods-price skeleton"></view>
                <view class="verified-price skeleton"></view>
              </view>
            </view>
            <view class="add skeleton"></view>
          </view>
        </view>

        <scroll-view
          v-else
          scroll-y
          class="goods-scroll"
          :scroll-into-view="scrollAnchor"
          :lower-threshold="10"
          @scroll="onGoodsScroll"
          @scrolltolower="onScrollLower"
          @touchstart="onGoodsTouchStart"
          @touchmove="onGoodsTouchMove"
          @touchend="onGoodsTouchEnd"
          @touchcancel="onGoodsTouchEnd"
        >
          <view class="goods-inner">
            <view id="goods-top"></view>
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
            <view v-if="nextCategory && !keyword.trim()" class="load-next" :class="{ ready: nextCategoryReady }">
              <text class="load-next-text">{{ nextCategoryReady ? `松开进入「${nextCategory.name}」` : `上滑进入「${nextCategory.name}」` }}</text>
            </view>
          </view>
        </scroll-view>
      </view>
    </view>

    <float-cart :count="cartTotal" />
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

.load-next {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 28rpx 0 44rpx;
  color: #bbb;
  font-size: 24rpx;
  letter-spacing: 1rpx;
  transition: color 0.15s ease;
}

.load-next.ready {
  color: #ff9a00;
  font-weight: 700;
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

/* 骨架屏样式 */
.goods-row .skeleton {
  border-radius: 16rpx;
}
.goods-row .goods-img.skeleton {
  border-radius: 20rpx;
}
.goods-row .goods-name.skeleton {
  height: 44rpx;
  width: 100%;
  border-radius: 8rpx;
}
.goods-row .goods-desc.skeleton,
.goods-row .goods-status.skeleton {
  margin-top: 8rpx;
  height: 32rpx;
  width: 80%;
  border-radius: 8rpx;
}
.goods-row .goods-price.skeleton {
  height: 44rpx;
  width: 140rpx;
  border-radius: 8rpx;
}
.goods-row .verified-price.skeleton {
  margin-top: 4rpx;
  height: 28rpx;
  width: 180rpx;
  border-radius: 8rpx;
}
.goods-row .add.skeleton {
  border-radius: 18rpx;
}
</style>
