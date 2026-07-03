<script setup>
import { computed, onMounted, ref, shallowRef } from 'vue'
import { onLoad, onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { addCartItem, cartCount } from '../../utils/cart.js'
import { fruitIcon, money, statusLabel } from '../../utils/format.js'
import { request } from '../../utils/request.js'
import { hasCustomerLogin } from '../../utils/auth.js'

const fruitId = shallowRef('')
const fruit = shallowRef(null)
const customer = shallowRef(null)
const loading = shallowRef(false)
const cartTotal = shallowRef(0)
const quantity = shallowRef(1)

const coverUrl = computed(() => fruit.value?.image_url || fruit.value?.image_urls?.[0] || '')
const galleryImageUrls = computed(() => {
  if (fruit.value?.image_urls?.length) return fruit.value.image_urls
  return coverUrl.value ? [coverUrl.value] : []
})
const detailImageUrls = computed(() => {
  if (fruit.value?.detail_image_urls?.length) return fruit.value.detail_image_urls
  return fruit.value?.image_urls?.length > 1 ? fruit.value.image_urls.slice(1) : []
})
const allPreviewImages = computed(() => [...galleryImageUrls.value, ...detailImageUrls.value])
const isVerified = computed(() => customer.value?.verification_status === 'verified')
const normalPrice = computed(() => Number(fruit.value?.quote?.normal_price || 0))
const verifiedPrice = computed(() => Number(fruit.value?.quote?.verified_price || 0))
const activePrice = computed(() => isVerified.value ? verifiedPrice.value : normalPrice.value)
const estimatedTotal = computed(() => activePrice.value * Number(quantity.value || 0))

function displayVerifiedPrice(price) {
  return isVerified.value ? `¥${money(price)}` : '???'
}
const productMeta = computed(() => [
  fruit.value?.origin,
  fruit.value?.spec,
  fruit.value?.quote?.grade,
].filter(Boolean).join(' · '))

async function loadFruit() {
  if (!fruitId.value) return
  loading.value = true
  try {
    fruit.value = await request({ url: `/fruits/${fruitId.value}` })
    quantity.value = Number(fruit.value?.quote?.min_order_quantity || 1)
  } catch (err) {
    uni.showToast({ title: err.message || '商品加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

async function loadCustomer() {
  if (!hasCustomerLogin()) {
    customer.value = null
    return
  }
  try {
    customer.value = await request({ url: '/customers/me' })
    uni.setStorageSync('verification_status', customer.value?.verification_status || 'unverified')
  } catch (err) {
    customer.value = null
  }
}

function changeQuantity(delta) {
  const min = Number(fruit.value?.quote?.min_order_quantity || 1)
  quantity.value = Math.max(min, Number(quantity.value || min) + delta)
}

function addToCart() {
  if (!fruit.value) return
  addCartItem(fruit.value, quantity.value)
  cartTotal.value = cartCount()
  uni.showToast({ title: '已加入预订车', icon: 'success' })
}

function reserveNow() {
  if (!fruit.value) return
  addToCart()
  uni.setStorageSync('checkout_items', JSON.stringify([{ ...fruit.value, quantity: quantity.value }]))
  uni.navigateTo({ url: '/pages/order/create?cart=1' })
}

function goCart() {
  uni.switchTab({ url: '/pages/cart/index' })
}

function goVerify() {
  uni.navigateTo({ url: '/pages/verify/index' })
}

function previewImages(current) {
  if (!allPreviewImages.value.length) return
  uni.previewImage({ urls: allPreviewImages.value, current })
}

onLoad((query) => {
  fruitId.value = query.id || ''
  loadFruit()
})

onMounted(loadCustomer)
onShow(() => {
  cartTotal.value = cartCount()
  loadCustomer()
})

onPullDownRefresh(async () => {
  try {
    await Promise.all([loadFruit(), loadCustomer()])
    cartTotal.value = cartCount()
  } finally {
    uni.stopPullDownRefresh()
  }
})

function onShareAppMessage() {
  return {
    title: fruit.value ? `${fruit.value.name} - 珍果链` : '珍果链 - 优质水果批发预订',
    path: `/pages/product/detail?id=${fruitId.value}`,
    imageUrl: coverUrl.value || ''
  }
}

function onShareTimeline() {
  return {
    title: fruit.value ? `${fruit.value.name} - 珍果链 - 优质水果批发预订` : '珍果链 - 优质水果批发预订',
    query: `id=${fruitId.value}`,
    imageUrl: coverUrl.value || ''
  }
}

defineExpose({
  onShareAppMessage,
  onShareTimeline
})
</script>

<template>
  <view class="page">

    <view class="gallery-card">
      <swiper v-if="galleryImageUrls.length" class="swiper" circular indicator-dots indicator-color="rgba(0,0,0,.18)" indicator-active-color="#ffb700">
        <swiper-item v-for="url in galleryImageUrls" :key="url">
          <image class="photo" :src="url" mode="aspectFill" @tap="previewImages(url)" />
        </swiper-item>
      </swiper>
      <view v-else class="emoji-photo">{{ fruitIcon(fruit?.name || '') }}</view>
    </view>

    <view class="info-card">
      <view class="title-row">
        <view class="name">{{ fruit?.name || '加载中' }}</view>
        <view class="stock">{{ statusLabel(fruit?.stock_status) }}</view>
      </view>
      <view v-if="productMeta" class="spec">{{ productMeta }}</view>
      <view class="price-row">
        <view class="price-box normal">
          <text class="price-label">普通价</text>
          <text class="price">¥{{ money(normalPrice) }}/{{ fruit?.unit || '斤' }}</text>
        </view>
        <view class="price-box verified">
          <text class="price-label">认证价</text>
          <text class="price">{{ displayVerifiedPrice(verifiedPrice) }}/{{ fruit?.unit || '斤' }}</text>
        </view>
      </view>
      <view class="auth-tip" @tap="goVerify">
        {{ isVerified ? '你已是认证客户，本单按认证价预估' : '认证店铺后可按认证价预订，点击去认证 ›' }}
      </view>
    </view>

    <view class="detail-card">
      <view class="section-title">商品说明</view>
      <view class="detail-line">起订量：{{ fruit?.quote?.min_order_quantity || 1 }}{{ fruit?.unit || '' }}</view>
      <view class="detail-line">价格说明：行情波动较快，提交预订后由供应商最终确认。</view>
      <view class="detail-line">商品备注：{{ fruit?.quote?.note || '支持批发预订，具体配送时间请联系供应商确认。' }}</view>
    </view>

    <view v-if="detailImageUrls.length" class="image-detail-card">
      <view class="section-title">商品详情实拍</view>
      <view class="image-tip">共 {{ detailImageUrls.length }} 张，点击可放大查看</view>
      <image
        v-for="url in detailImageUrls"
        :key="url"
        class="detail-image"
        :src="url"
        mode="widthFix"
        @tap="previewImages(url)"
      />
    </view>

    <view class="quantity-card">
      <view>
        <view class="section-title">预订数量</view>
        <view class="detail-line">预估合计 <text class="total">¥{{ money(estimatedTotal) }}</text></view>
      </view>
      <view class="stepper">
        <button class="step" @tap="changeQuantity(-1)">−</button>
        <text class="quantity">{{ quantity }}</text>
        <button class="step" @tap="changeQuantity(1)">＋</button>
      </view>
    </view>

    <view class="bottom-bar">
      <view class="cart-link" @tap="goCart">
        <text class="cart-icon">🛒</text>
        <text v-if="cartTotal" class="cart-badge">{{ cartTotal }}</text>
        <text class="cart-text">购物车</text>
      </view>
      <button class="cart-button" @tap="addToCart">加入购物车</button>
      <button class="reserve-button" @tap="reserveNow">立即预订</button>
    </view>
  </view>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding-bottom: 132rpx;
  background: #f3f3f3;
}





.gallery-card,
.info-card,
.detail-card,
.image-detail-card,
.quantity-card {
  margin: 24rpx 26rpx 0;
  border-radius: 22rpx;
  background: #fff;
}

.gallery-card {
  overflow: hidden;
}

.swiper,
.photo,
.emoji-photo {
  width: 100%;
  height: 520rpx;
}

.photo {
  display: block;
}

.emoji-photo {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 180rpx;
  background: #fafafa;
}

.info-card,
.detail-card,
.image-detail-card,
.quantity-card {
  padding: 28rpx;
  box-sizing: border-box;
}

.title-row,
.quantity-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
}

.name {
  flex: 1;
  color: #222;
  font-size: 40rpx;
  font-weight: 900;
  line-height: 1.3;
}

.stock {
  flex-shrink: 0;
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  color: #ff8a00;
  background: #fff3d2;
  font-size: 24rpx;
}

.spec,
.detail-line {
  margin-top: 14rpx;
  color: #888;
  font-size: 26rpx;
  line-height: 1.55;
}

.price-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18rpx;
  margin-top: 26rpx;
}

.price-box {
  padding: 22rpx;
  border-radius: 18rpx;
  background: #f7f7f7;
}

.price-box.verified {
  background: #fff4dc;
}

.price-label {
  display: block;
  color: #888;
  font-size: 24rpx;
}

.price {
  display: block;
  margin-top: 10rpx;
  color: #f20d2f;
  font-size: 38rpx;
  font-weight: 900;
}

.auth-tip {
  margin-top: 24rpx;
  padding: 18rpx 22rpx;
  border-radius: 16rpx;
  color: #ff5a00;
  background: #fff2df;
  font-size: 26rpx;
}

.section-title {
  color: #222;
  font-size: 32rpx;
  font-weight: 900;
}

.image-tip {
  margin-top: 10rpx;
  color: #999;
  font-size: 24rpx;
}

.detail-image {
  display: block;
  width: 100%;
  margin-top: 20rpx;
  border-radius: 18rpx;
  background: #f6f6f6;
}

.total {
  color: #f20d2f;
  font-size: 34rpx;
  font-weight: 900;
}

.stepper {
  display: flex;
  align-items: center;
  height: 58rpx;
  overflow: hidden;
  border-radius: 12rpx;
  background: #f1f2f4;
}

.step {
  width: 58rpx;
  height: 58rpx;
  line-height: 54rpx;
  color: #333;
  background: transparent;
  font-size: 38rpx;
}

.quantity {
  min-width: 64rpx;
  text-align: center;
  color: #222;
  font-size: 30rpx;
}

.bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: var(--window-bottom);
  display: flex;
  align-items: center;
  gap: 16rpx;
  height: 112rpx;
  padding: 0 24rpx;
  border-top: 1rpx solid #eee;
  background: #fff;
  box-sizing: border-box;
}

.cart-link {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100rpx;
  color: #666;
  font-size: 22rpx;
}

.cart-icon {
  font-size: 38rpx;
}

.cart-badge {
  position: absolute;
  right: 12rpx;
  top: -2rpx;
  min-width: 28rpx;
  height: 28rpx;
  line-height: 28rpx;
  border-radius: 999rpx;
  text-align: center;
  color: #fff;
  background: #f20d2f;
  font-size: 18rpx;
}

.cart-button,
.reserve-button {
  flex: 1;
  height: 74rpx;
  line-height: 74rpx;
  border-radius: 999rpx;
  color: #fff;
  font-size: 29rpx;
  font-weight: 800;
}

.cart-button {
  background: #ffc766;
}

.reserve-button {
  background: #ffb700;
}
</style>
