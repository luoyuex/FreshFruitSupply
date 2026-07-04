<script setup>
import { computed, onMounted, shallowRef } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { statusLabel } from '../../utils/format.js'
import { request } from '../../utils/request.js'
import { hasCustomerLogin, isPlaceholderPhone, loginWithWeChat, logoutCustomer } from '../../utils/auth.js'
import { openAdminHome } from '../../utils/admin.js'

const phone = shallowRef(uni.getStorageSync('customer_phone') || '')
const customer = shallowRef(null)
const orders = shallowRef([])
const loading = shallowRef(false)
const loggedIn = shallowRef(hasCustomerLogin())
const adminEntryVisible = shallowRef(false)

const isLoggedIn = computed(() => loggedIn.value)
const displayName = computed(() => {
  if (!isLoggedIn.value) return '未登录'
  if (customer.value?.nickname) return customer.value.nickname
  if (customer.value?.shop_name) return customer.value.shop_name
  return phone.value ? `鲜小店${phone.value.slice(-4)}` : '微信用户'
})
const orderStats = computed(() => ({
  pending: orders.value.filter((item) => item.status === 'pending').length,
  confirmed: orders.value.filter((item) => item.status === 'confirmed').length,
  delivering: orders.value.filter((item) => item.status === 'delivering').length,
}))

async function loadMine() {
  loggedIn.value = hasCustomerLogin()
  phone.value = uni.getStorageSync('customer_phone') || ''
  if (!hasCustomerLogin()) {
    customer.value = null
    orders.value = []
    adminEntryVisible.value = false
    return
  }
  loading.value = true
  try {
    customer.value = await request({ url: '/customers/me' })
    if (!isPlaceholderPhone(customer.value?.phone)) {
      phone.value = customer.value.phone
      uni.setStorageSync('customer_phone', customer.value.phone)
    } else {
      phone.value = ''
      uni.removeStorageSync('customer_phone')
    }
    uni.setStorageSync('verification_status', customer.value?.verification_status || 'unverified')
    const [myOrders, adminEntry] = await Promise.all([
      request({ url: '/orders/my' }),
      request({ url: '/admin/entry-visible' }).catch(() => ({ visible: false })),
    ])
    orders.value = myOrders
    adminEntryVisible.value = Boolean(adminEntry.visible)
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
  } finally {
    loading.value = false
  }
}

async function goVerify() {
  if (!(await ensureLogin())) return
  uni.navigateTo({ url: '/pages/verify/index' })
}

async function ensureLogin() {
  if (hasCustomerLogin()) return true
  loading.value = true
  try {
    const data = await loginWithWeChat()
    customer.value = data.customer
    if (!isPlaceholderPhone(data.customer?.phone)) phone.value = data.customer.phone
    loggedIn.value = true
    uni.showToast({ title: '登录成功', icon: 'success' })
    return true
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
    return false
  } finally {
    loading.value = false
  }
}

async function goProfile() {
  if (!(await ensureLogin())) return
  uni.navigateTo({ url: '/pages/profile/detail' })
}

function goAdmin() {
  openAdminHome()
}

async function goOrders(status = '') {
  if (!(await ensureLogin())) return
  uni.navigateTo({ url: `/pages/order/list${status ? `?status=${status}` : ''}` })
}

async function goAddress() {
  if (!(await ensureLogin())) return
  uni.navigateTo({ url: '/pages/address/index' })
}

function goAgreement() {
  uni.navigateTo({ url: '/pages/agreement/index' })
}

function logout() {
  uni.showModal({
    title: '退出登录',
    content: '退出后会清除本地登录状态和购物车，再登录会按微信身份读取真实用户信息。',
    success: (res) => {
      if (!res.confirm) return
      logoutCustomer()
      loggedIn.value = false
      phone.value = ''
      customer.value = null
      orders.value = []
      adminEntryVisible.value = false
      uni.showToast({ title: '已退出', icon: 'success' })
    },
  })
}

onMounted(loadMine)
onShow(loadMine)

onPullDownRefresh(async () => {
  try {
    await loadMine()
  } finally {
    uni.stopPullDownRefresh()
  }
})

function onShareAppMessage() {
  return {
    title: '珍果链 - 个人中心',
    path: '/pages/mine/index',
    imageUrl: ''
  }
}

function onShareTimeline() {
  return {
    title: '珍果链 - 个人中心',
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

    <view class="profile-head" @tap="goProfile">
      <view class="logo-mark">
        <image v-if="customer?.avatar_url" class="avatar-img" :src="customer.avatar_url" mode="aspectFill" />
        <text v-else>🍊</text>
      </view>
      <view class="profile-main">
        <view class="name-row">
          <text class="shop-name">{{ displayName }}</text>
          <button class="verify-badge" @tap.stop="goVerify">{{ statusLabel(customer?.verification_status || 'unverified') }} ›</button>
        </view>
        <view class="account">{{ isLoggedIn ? (phone ? `账号名：${phone}` : '已登录，手机号可选绑定') : '点击登录后查看个人信息' }}</view>
      </view>
      <view class="icon-row">
        <image class="header-icon" src="/static/icons/mail.svg" mode="aspectFit" />
      </view>
    </view>

    <view class="coupon-card">
      <view class="coupon-number">0张</view>
      <view class="coupon-label">红包/卡券</view>
    </view>

    <view class="order-card">
      <view class="card-head">
        <text class="card-title">我的订单</text>
        <text class="all-order" @tap="goOrders()">全部订单 ›</text>
      </view>
      <view class="order-icons">
        <view class="order-icon" @tap="goOrders('pending')">
          <image class="line-icon" src="/static/icons/clock-3.svg" mode="aspectFit" />
          <text>待确认</text>
          <view v-if="orderStats.pending" class="dot">{{ orderStats.pending }}</view>
        </view>
        <view class="order-icon" @tap="goOrders('confirmed')">
          <image class="line-icon" src="/static/icons/order-confirmed.svg" mode="aspectFit" />
          <text>已确认</text>
          <view v-if="orderStats.confirmed" class="dot">{{ orderStats.confirmed }}</view>
        </view>
        <view class="order-icon" @tap="goOrders('delivering')">
          <image class="line-icon" src="/static/icons/truck.svg" mode="aspectFit" />
          <text>配送中</text>
          <view v-if="orderStats.delivering" class="dot">{{ orderStats.delivering }}</view>
        </view>
        <view class="order-icon" @tap="goOrders('completed')">
          <image class="line-icon" src="/static/icons/circle-check-big.svg" mode="aspectFit" />
          <text>已完成</text>
        </view>
      </view>
    </view>

    <view class="tool-card">
      <view class="tool" @tap="goAddress">
        <image class="tool-icon" src="/static/icons/map-pin-dark.svg" mode="aspectFit" />
        <text>地址管理</text>
      </view>
      <view class="tool" @tap="goVerify">
        <image class="tool-icon" src="/static/icons/badge-check.svg" mode="aspectFit" />
        <text>认证资料</text>
      </view>
      <view class="tool" @tap="goAgreement">
        <image class="tool-icon" src="/static/icons/file-text-dark.svg" mode="aspectFit" />
        <text>用户协议</text>
      </view>
    </view>

    <view v-if="adminEntryVisible" class="admin-card" @tap="goAdmin">
      <image class="admin-icon" src="/static/icons/store-backend.svg" mode="aspectFit" />
      <view>
        <view class="admin-title">供应商后台</view>
        <view class="admin-sub">仅管理员可见，用于处理订单和报价。</view>
      </view>
      <text class="admin-arrow">›</text>
    </view>

    <view class="logout-card" @tap="logout">
      <image class="logout-icon" src="/static/icons/log-out.svg" mode="aspectFit" />
      <text>退出登录</text>
    </view>
  </view>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding-bottom: 40rpx;
  background: #f3f3f3;
}





.profile-head {
  display: flex;
  align-items: center;
  gap: 28rpx;
  padding: 74rpx 36rpx 46rpx;
  background: #fff;
}

.logo-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 112rpx;
  height: 112rpx;
  border-radius: 50%;
  background: #fff7e5;
  font-size: 74rpx;
  overflow: hidden;
}

.avatar-img {
  width: 100%;
  height: 100%;
}

.profile-main {
  flex: 1;
  min-width: 0;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.shop-name {
  color: #333;
  font-size: 36rpx;
  font-weight: 900;
}

.verify-badge {
  height: 44rpx;
  line-height: 44rpx;
  padding: 0 14rpx;
  border-radius: 8rpx;
  color: #fff;
  background: #ffb700;
  font-size: 24rpx;
}

.account {
  margin-top: 18rpx;
  color: #666;
  font-size: 30rpx;
}

.icon-row {
  display: flex;
  gap: 28rpx;
}

.header-icon {
  width: 44rpx;
  height: 44rpx;
}

.phone-card,
.coupon-card,
.order-card,
.tool-card,
.admin-card,
.logout-card {
  margin: 24rpx 26rpx 0;
  border-radius: 22rpx;
  background: #fff;
}

.phone-card {
  display: flex;
  gap: 14rpx;
  padding: 18rpx;
  border-radius: 20rpx;
}

.phone-input {
  flex: 1;
  height: 68rpx;
  padding: 0 18rpx;
  border-radius: 14rpx;
  background: #f6f6f6;
  font-size: 26rpx;
}

.query {
  width: 132rpx;
  height: 68rpx;
  line-height: 68rpx;
  border-radius: 999rpx;
  color: #fff;
  background: #ffb700;
  font-size: 26rpx;
}

.coupon-card {
  padding: 38rpx;
  text-align: center;
}

.coupon-number {
  color: #111;
  font-size: 40rpx;
}

.coupon-label {
  margin-top: 14rpx;
  color: #666;
  font-size: 28rpx;
}

.order-card {
  padding: 34rpx 26rpx 28rpx;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  color: #333;
  font-size: 32rpx;
  font-weight: 900;
}

.all-order {
  color: #777;
  font-size: 27rpx;
}

.order-icons {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  margin-top: 38rpx;
}

.order-icon {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;
  color: #333;
  font-size: 26rpx;
}

.line-icon {
  width: 54rpx;
  height: 54rpx;
}

.dot {
  position: absolute;
  top: -8rpx;
  right: 32rpx;
  min-width: 28rpx;
  height: 28rpx;
  line-height: 28rpx;
  border-radius: 999rpx;
  text-align: center;
  color: #fff;
  background: #f20d2f;
  font-size: 18rpx;
}

.tool-card {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  padding: 38rpx 10rpx 40rpx;
}

.tool {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14rpx;
  color: #333;
  font-size: 25rpx;
}

.tool-icon {
  width: 56rpx;
  height: 56rpx;
}

.admin-card {
  display: flex;
  align-items: center;
  gap: 18rpx;
  padding: 24rpx 28rpx;
}

.admin-icon {
  width: 50rpx;
  height: 50rpx;
}

.admin-title {
  color: #333;
  font-size: 29rpx;
  font-weight: 900;
}

.admin-sub {
  margin-top: 8rpx;
  color: #777;
  font-size: 24rpx;
}

.admin-arrow {
  margin-left: auto;
  color: #999;
  font-size: 38rpx;
}

.logout-card {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14rpx;
  height: 92rpx;
  color: #ef4444;
  font-size: 28rpx;
  font-weight: 700;
}

.logout-icon {
  width: 40rpx;
  height: 40rpx;
}
</style>
