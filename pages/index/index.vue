<script setup>
import { computed, onMounted, shallowRef } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { useFruitQuotes } from '../../composables/useFruitQuotes.js'
import { fruitIcon, money, statusLabel } from '../../utils/format.js'
import { request } from '../../utils/request.js'
import { addCartItem, cartCount } from '../../utils/cart.js'
import { hasCustomerLogin } from '../../utils/auth.js'
import { categoryIconPath } from '../../utils/categoryIcons.js'

const { loading, error, keyword, activeCategory, categoryItems, visibleFruits, fruits, loadFruits } = useFruitQuotes()
const customer = shallowRef(null)
const cartTotal = shallowRef(0)
const announcementItems = shallowRef([])
const announcementVisible = shallowRef(false)

const isVerified = computed(() => customer.value?.verification_status === 'verified')
const showVerifyGuide = computed(() => !isVerified.value)
const featuredFruits = computed(() => fruits.value.slice(0, 4))
const fruitCategories = computed(() => categoryItems.value.slice(0, 8))

function displayVerifiedPrice(price) {
  return isVerified.value ? `¥${money(price)}` : '???'
}

function categoryInitial(name = '') {
  return String(name).trim().slice(0, 1) || '果'
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

// 公告：登录用户进首页时，有未读则自动弹最新公告；关闭即标记已读
async function loadAnnouncements() {
  if (!hasCustomerLogin()) return
  try {
    const feed = await request({ url: '/announcements' })
    announcementItems.value = feed.items || []
    if (Number(feed.unread_count) > 0) {
      announcementVisible.value = true
    }
  } catch (err) {
    // 公告拉取失败不影响首页正常使用
  }
}

async function closeAnnouncement() {
  announcementVisible.value = false
  try {
    await request({ url: '/announcements/read', method: 'POST' })
  } catch (err) {
    // 标记已读失败无妨，下次进入仍会重试
  }
}

function selectCategory(category) {
  activeCategory.value = category
  uni.setStorageSync('active_category', category)
  uni.switchTab({ url: '/pages/category/index' })
}

function goVerify() {
  uni.navigateTo({ url: '/pages/verify/index' })
}

function primaryImage(fruit) {
  return fruit.image_urls?.[0] || fruit.image_url || ''
}

function goDetail(fruit) {
  uni.navigateTo({ url: `/pages/product/detail?id=${fruit.id}` })
}

function addToCart(fruit) {
  addCartItem(fruit, Number(fruit.quote?.min_order_quantity || 1))
  cartTotal.value = cartCount()
  uni.showToast({ title: '已加入预订车', icon: 'success' })
}

function goCategory() {
  uni.switchTab({ url: '/pages/category/index' })
}

onMounted(() => {
  loadFruits()
  loadCustomer()
  loadAnnouncements()
})

onShow(() => {
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
    title: '珍果链 - 优质水果批发预订',
    path: '/pages/index/index',
    imageUrl: ''
  }
}

function onShareTimeline() {
  return {
    title: '珍果链 - 优质水果批发预订',
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

    <view class="category-card">
      <view v-for="category in fruitCategories" :key="category.id" class="category-item" @tap="selectCategory(category.name)">
        <view v-if="category.icon_url" class="category-photo">
          <image class="category-icon-img" :src="category.icon_url" mode="aspectFill" />
        </view>
        <view v-else-if="categoryIconPath(category.icon)" class="category-photo">
          <image class="category-icon-img" :src="categoryIconPath(category.icon)" mode="aspectFit" />
        </view>
        <view v-else class="category-text-photo">{{ categoryInitial(category.name) }}</view>
        <text class="category-name">{{ category.name }}</text>
      </view>
      <view class="category-item" @tap="selectCategory('全部')">
        <view class="category-photo all">果</view>
        <text class="category-name">全部水果</text>
      </view>
    </view>

    <view v-if="showVerifyGuide" class="verify-card" @tap="goVerify">
      <view>
        <view class="verify-title">认证后享认证价</view>
        <view class="verify-sub">店铺认证通过后，下单自动按认证价预估。</view>
      </view>
      <button class="verify-link" @tap.stop="goVerify">去认证</button>
    </view>

    <view class="section-head">
      <text class="section-title">{{ keyword ? '搜索结果' : '今日优选' }}</text>
      <text v-if="!keyword" class="section-more" @tap="goCategory">全部商品 ›</text>
    </view>

    <view v-if="error" class="notice">后端连接失败，请确认 Python 服务和数据库已启动</view>

    <!-- 骨架屏 -->
    <view v-if="loading" class="goods-grid">
      <view v-for="i in 4" :key="i" class="goods-card">
        <view class="goods-photo skeleton"></view>
        <view class="goods-name skeleton"></view>
        <view class="goods-spec skeleton"></view>
        <view class="goods-bottom">
          <view class="price-stack">
            <view class="goods-price skeleton"></view>
            <view class="verified-price skeleton"></view>
          </view>
          <view class="plus skeleton"></view>
        </view>
      </view>
    </view>

    <view v-else class="goods-grid">
      <view v-for="fruit in (keyword ? visibleFruits : featuredFruits)" :key="fruit.id" class="goods-card" @tap="goDetail(fruit)">
        <view class="goods-photo">
          <image v-if="primaryImage(fruit)" class="goods-image" :src="primaryImage(fruit)" mode="aspectFill" />
          <text v-else>{{ fruitIcon(fruit.name) }}</text>
          <view v-if="fruit.stock_status === 'out_of_stock'" class="sold-out-mask">
            <text class="sold-out-text">售罄</text>
          </view>
        </view>
        <view class="goods-name">{{ fruit.name }}</view>
        <view class="goods-spec">{{ fruit.spec }}</view>
        <view class="goods-bottom">
          <view class="price-stack">
            <text class="goods-price">¥{{ money(fruit.quote?.normal_price) }}</text>
            <text class="verified-price">认证价 {{ displayVerifiedPrice(fruit.quote?.verified_price) }}</text>
          </view>
          <view class="plus" @tap.stop="addToCart(fruit)"><view class="plus-line horizontal"></view><view class="plus-line vertical"></view></view>
        </view>
      </view>
    </view>
    
    <view v-if="keyword && visibleFruits.length === 0" class="empty-result">
      <text class="empty-text">未找到相关商品</text>
    </view>

    <float-cart :count="cartTotal" />

    <announcement-modal :visible="announcementVisible" :items="announcementItems" @close="closeAnnouncement" />
  </view>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding: 0 26rpx 40rpx;
  background: #f3f3f3;
  box-sizing: border-box;
}





.search-wrap {
  display: flex;
  align-items: center;
  height: 80rpx;
  margin: 24rpx 0 28rpx;
  padding: 0 28rpx;
  border-radius: 999rpx;
  background: #fff;
}

.search-icon {
  margin-right: 14rpx;
  color: #a8a8a8;
  font-size: 40rpx;
}

.search-input {
  flex: 1;
  height: 80rpx;
  font-size: 30rpx;
  color: #222;
}

.category-card {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  row-gap: 28rpx;
  padding: 28rpx 10rpx 26rpx;
  border-radius: 22rpx;
  background: #fff;
}

.category-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.category-photo,
.category-text-photo {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 86rpx;
  height: 86rpx;
  border-radius: 50%;
  background: #fff8e8;
}

.category-text-photo {
  color: #8a5a00;
  font-size: 36rpx;
  font-weight: 900;
}

.category-icon-img {
  width: 58rpx;
  height: 58rpx;
}

.category-photo.all {
  color: #fff;
  font-size: 34rpx;
  font-weight: 800;
  background: #ffb700;
}

.category-name {
  margin-top: 12rpx;
  color: #2b2b2b;
  font-size: 26rpx;
}

.verify-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  margin-top: 22rpx;
  padding: 24rpx 26rpx;
  border-radius: 22rpx;
  background: #fffaf0;
  border: 2rpx solid #ffe0a3;
}

.verify-title {
  color: #222;
  font-size: 30rpx;
  font-weight: 900;
}

.verify-sub {
  margin-top: 8rpx;
  color: #777;
  font-size: 24rpx;
  line-height: 1.4;
}

.verify-link {
  flex-shrink: 0;
  width: 142rpx;
  height: 62rpx;
  line-height: 62rpx;
  border-radius: 999rpx;
  color: #fff;
  background: #ffb700;
  font-size: 25rpx;
  font-weight: 900;
}

.verify-link::after {
  border: none;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 28rpx 0 18rpx;
}

.section-title {
  color: #222;
  font-size: 34rpx;
  font-weight: 800;
}

.section-more {
  color: #888;
  font-size: 25rpx;
}

.notice {
  margin-bottom: 16rpx;
  padding: 18rpx 22rpx;
  border-radius: 18rpx;
  color: #ff6a00;
  background: #fff4e4;
  font-size: 24rpx;
}

.goods-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 18rpx;
}

.goods-card {
  min-height: 360rpx;
  padding: 24rpx;
  border-radius: 20rpx;
  background: #fff;
  box-sizing: border-box;
}

.goods-photo {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 158rpx;
  overflow: hidden;
  font-size: 96rpx;
  background: #fafafa;
  border-radius: 16rpx;
}

.goods-image {
  width: 100%;
  height: 100%;
}

.goods-name {
  margin-top: 18rpx;
  color: #222;
  font-size: 28rpx;
  font-weight: 700;
}

.goods-spec {
  height: 64rpx;
  margin-top: 8rpx;
  color: #8b8b8b;
  font-size: 23rpx;
  line-height: 1.4;
}

.goods-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12rpx;
}

.price-stack {
  display: flex;
  flex-direction: column;
}

.goods-price {
  color: #f20d2f;
  font-size: 32rpx;
  font-weight: 900;
}

.verified-price {
  margin-top: 4rpx;
  color: #ff8a00;
  font-size: 22rpx;
  font-weight: 700;
}

.plus {
  position: relative;
  width: 58rpx;
  height: 58rpx;
  border-radius: 18rpx;
  background: #ffb700;
}

.plus-line {
  position: absolute;
  left: 50%;
  top: 50%;
  border-radius: 999rpx;
  background: #fff;
  transform: translate(-50%, -50%);
}

.plus-line.horizontal {
  width: 28rpx;
  height: 6rpx;
}

.plus-line.vertical {
  width: 6rpx;
  height: 28rpx;
}

/* 骨架屏样式 */
.goods-card .skeleton {
  border-radius: 16rpx;
}
.goods-card .goods-photo.skeleton {
  height: 158rpx;
}
.goods-card .goods-name.skeleton {
  margin-top: 18rpx;
  height: 32rpx;
  border-radius: 8rpx;
}
.goods-card .goods-spec.skeleton {
  margin-top: 8rpx;
  height: 64rpx;
  border-radius: 8rpx;
}
.goods-card .goods-price.skeleton {
  height: 36rpx;
  width: 120rpx;
  border-radius: 8rpx;
}
.goods-card .verified-price.skeleton {
  margin-top: 4rpx;
  height: 24rpx;
  width: 160rpx;
  border-radius: 8rpx;
}
.goods-card .plus.skeleton {
  border-radius: 18rpx;
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
  border-radius: 16rpx;
}

.sold-out-text {
  color: #fff;
  font-size: 32rpx;
  font-weight: 900;
  letter-spacing: 4rpx;
}

.empty-result {
  margin-top: 40rpx;
  padding: 60rpx 20rpx;
  text-align: center;
}

.empty-text {
  color: #999;
  font-size: 28rpx;
}
</style>
