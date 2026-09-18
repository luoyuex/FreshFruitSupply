<script setup>
import { computed, shallowRef } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { addCartItem, cartCount } from '../../utils/cart.js'
import { fruitIcon, money, statusLabel } from '../../utils/format.js'
import { hasCustomerLogin, loginWithWeChat } from '../../utils/auth.js'
import { request } from '../../utils/request.js'
import { flags } from '../../utils/flags.js'
import { refreshCustomTabBar } from '../../utils/tabBar.js'

const items = shallowRef([])
const loading = shallowRef(false)
const cartTotal = shallowRef(0)
const loggedIn = shallowRef(hasCustomerLogin())
const customer = shallowRef(null)

const isVerified = computed(() => customer.value?.verification_status === 'verified')

function displayVerifiedPrice(price) {
  return isVerified.value ? `¥${money(price)}` : '???'
}

async function loadFrequentItems() {
  loggedIn.value = hasCustomerLogin()
  if (!loggedIn.value) {
    items.value = []
    customer.value = null
    return
  }
  loading.value = true
  try {
    const [data, me] = await Promise.all([
      request({ url: '/frequent-items?limit=20' }),
      request({ url: '/customers/me' }).catch(() => null),
    ])
    items.value = data || []
    customer.value = me
  } catch (err) {
    items.value = []
  } finally {
    loading.value = false
  }
}

async function ensureLogin() {
  if (hasCustomerLogin()) return true
  loading.value = true
  try {
    const data = await loginWithWeChat()
    customer.value = data.customer
    loggedIn.value = true
    refreshCustomTabBar()
    return true
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
    return false
  } finally {
    loading.value = false
  }
}

function primaryImage(fruit) {
  return fruit.image_url || fruit.image_urls?.[0] || ''
}

function goDetail(fruit) {
  uni.navigateTo({ url: `/pages/product/detail?id=${fruit.fruit_id}` })
}

function addToCart(fruit) {
  addCartItem(
    {
      id: fruit.fruit_id,
      name: fruit.fruit_name,
      category: fruit.category,
      image_url: fruit.image_url || fruit.image_urls?.[0] || '',
      image_urls: fruit.image_urls || [],
      spec: fruit.spec,
      unit: fruit.unit,
      stock_status: fruit.stock_status,
      quote: fruit.quote,
    },
    Number(fruit.quote?.min_order_quantity || 1),
  )
  cartTotal.value = cartCount()
  uni.showToast({ title: '已加入购物车', icon: 'success' })
}

function goCategory() {
  uni.switchTab({ url: '/pages/category/index' })
}

async function doLogin() {
  const ok = await ensureLogin()
  if (ok) {
    await loadFrequentItems()
  }
}

onShow(() => {
  cartTotal.value = cartCount()
  loadFrequentItems()
  refreshCustomTabBar()
})

onPullDownRefresh(async () => {
  try {
    await loadFrequentItems()
    cartTotal.value = cartCount()
  } finally {
    uni.stopPullDownRefresh()
  }
})

function onShareAppMessage() {
  return {
    title: '珍果链 - 常购清单',
    path: '/pages/frequent/index',
    imageUrl: '',
  }
}

function onShareTimeline() {
  return {
    title: '珍果链 - 常购清单',
    query: '',
    imageUrl: '',
  }
}

defineExpose({
  onShareAppMessage,
  onShareTimeline,
})
</script>

<template>
  <view class="page">

    <!-- 未登录 -->
    <view v-if="!loggedIn" class="empty-card">
      <view class="empty-icon">⭐</view>
      <view class="empty-title">登录后查看常购清单</view>
      <view class="empty-desc">根据您的历史订单，自动整理常买的水果</view>
      <button class="login-btn" @tap="doLogin">微信登录</button>
    </view>

    <!-- 已登录但无数据 -->
    <view v-else-if="!loading && items.length === 0" class="empty-card">
      <view class="empty-icon">📋</view>
      <view class="empty-title">还没有常购记录</view>
      <view class="empty-desc">下单后这里会自动展示您常买的水果</view>
      <button class="go-btn" @tap="goCategory">去逛逛</button>
    </view>

    <!-- 骨架屏 -->
    <view v-else-if="loading && items.length === 0" class="list-wrap">
      <view v-for="i in 5" :key="i" class="item-row">
        <view class="item-img skeleton"></view>
        <view class="item-info">
          <view class="item-name skeleton"></view>
          <view class="item-spec skeleton"></view>
          <view class="price-line">
            <view class="item-price skeleton"></view>
            <view class="verified-price skeleton"></view>
          </view>
        </view>
        <view class="item-add skeleton"></view>
      </view>
    </view>

    <!-- 数据列表 -->
    <view v-else class="list-wrap">
      <view class="section-head">
        <text class="section-title">常购商品</text>
        <text class="section-sub">按购买总数量排序</text>
      </view>
      <view
        v-for="fruit in items"
        :key="fruit.fruit_id"
        class="item-row"
        @tap="goDetail(fruit)"
      >
        <view class="item-img">
          <image v-if="primaryImage(fruit)" class="item-image" :src="primaryImage(fruit)" mode="aspectFill" />
          <text v-else>{{ fruitIcon(fruit.fruit_name) }}</text>
          <view v-if="fruit.stock_status === 'out_of_stock'" class="sold-out-mask">
            <text class="sold-out-text">售罄</text>
          </view>
        </view>
        <view class="item-info">
          <view class="item-name">{{ fruit.fruit_name }} {{ fruit.spec }}</view>
          <view class="item-stat">已购 {{ fruit.purchase_count }}{{ fruit.unit }} · {{ statusLabel(fruit.stock_status) }}</view>
          <view class="price-line">
            <text class="item-price">¥{{ money(fruit.quote?.normal_price) }}</text>
            <text v-if="flags.verification_enabled" class="verified-price">认证价 {{ displayVerifiedPrice(fruit.quote?.verified_price) }}</text>
          </view>
        </view>
        <view class="item-add" @tap.stop="addToCart(fruit)">
          <view class="add-line horizontal"></view>
          <view class="add-line vertical"></view>
        </view>
      </view>
    </view>

    <float-cart :count="cartTotal" />
  </view>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding-bottom: calc(140rpx + env(safe-area-inset-bottom));
  background: #f3f3f3;
  box-sizing: border-box;
}

/* 空状态 */
.empty-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 100rpx 26rpx 0;
  padding: 80rpx 40rpx;
  border-radius: 26rpx;
  text-align: center;
  background: #fff;
}

.empty-icon {
  font-size: 82rpx;
}

.empty-title {
  margin-top: 24rpx;
  color: #222;
  font-size: 32rpx;
  font-weight: 800;
}

.empty-desc {
  margin-top: 14rpx;
  color: #999;
  font-size: 26rpx;
  line-height: 1.5;
}

.login-btn,
.go-btn {
  width: 260rpx;
  height: 80rpx;
  line-height: 80rpx;
  margin-top: 36rpx;
  border-radius: 999rpx;
  color: #fff;
  background: #ffb700;
  font-size: 30rpx;
}

.login-btn::after,
.go-btn::after {
  border: none;
}

/* 列表区域 */
.list-wrap {
  padding: 0 26rpx 40rpx;
}

.section-head {
  display: flex;
  align-items: baseline;
  gap: 14rpx;
  margin: 26rpx 0 16rpx;
}

.section-title {
  color: #222;
  font-size: 32rpx;
  font-weight: 800;
}

.section-sub {
  color: #aaa;
  font-size: 23rpx;
}

/* 商品行 */
.item-row {
  position: relative;
  display: flex;
  gap: 22rpx;
  margin-top: 16rpx;
  padding: 24rpx 26rpx;
  border-radius: 22rpx;
  background: #fff;
}

.item-img {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 158rpx;
  height: 158rpx;
  overflow: hidden;
  border-radius: 18rpx;
  font-size: 92rpx;
  background: #fafafa;
}

.item-image {
  width: 100%;
  height: 100%;
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
  border-radius: 18rpx;
}

.sold-out-text {
  color: #fff;
  font-size: 28rpx;
  font-weight: 900;
  letter-spacing: 4rpx;
}

.item-info {
  flex: 1;
  min-width: 0;
  padding-right: 54rpx;
}

.item-name {
  color: #222;
  font-size: 30rpx;
  font-weight: 800;
  line-height: 1.45;
}

.item-stat {
  margin-top: 10rpx;
  color: #999;
  font-size: 24rpx;
}

.price-line {
  display: flex;
  flex-direction: column;
  margin-top: 18rpx;
}

.item-price {
  color: #f20d2f;
  font-size: 36rpx;
  font-weight: 900;
}

.verified-price {
  margin-top: 4rpx;
  color: #ff8a00;
  font-size: 23rpx;
  font-weight: 700;
}

.item-add {
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

/* 骨架屏 */
.item-row .skeleton {
  border-radius: 14rpx;
}

.item-row .item-img.skeleton {
  border-radius: 18rpx;
}

.item-row .item-name.skeleton {
  height: 38rpx;
  width: 100%;
  border-radius: 8rpx;
}

.item-row .item-spec.skeleton {
  margin-top: 10rpx;
  height: 28rpx;
  width: 60%;
  border-radius: 8rpx;
}

.item-row .item-price.skeleton {
  height: 40rpx;
  width: 130rpx;
  border-radius: 8rpx;
}

.item-row .verified-price.skeleton {
  margin-top: 4rpx;
  height: 24rpx;
  width: 170rpx;
  border-radius: 8rpx;
}

.item-row .item-add.skeleton {
  border-radius: 18rpx;
}
</style>
