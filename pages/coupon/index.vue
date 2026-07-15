<script setup>
import { computed, ref, shallowRef } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { dateTimeSec, money, statusLabel } from '../../utils/format.js'
import { isReissueCoupon } from '../../utils/coupon.js'
import { request } from '../../utils/request.js'
import { hasCustomerLogin, loginWithWeChat } from '../../utils/auth.js'

const tabs = [
  { key: 'unused', label: '未使用' },
  { key: 'used', label: '已使用' },
  { key: 'expired', label: '已过期' },
]

const coupons = ref([])
const activeStatus = shallowRef('unused')
const loading = shallowRef(false)
const loginChecked = shallowRef(false)

const filteredCoupons = computed(() => coupons.value.filter((coupon) => coupon.status === activeStatus.value))

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

async function loadCoupons() {
  if (!(await ensureLogin())) {
    coupons.value = []
    loginChecked.value = true
    return
  }
  loading.value = true
  try {
    const list = await request({ url: '/coupons/my' })
    coupons.value = Array.isArray(list) ? list : []
  } catch (err) {
    uni.showToast({ title: err.message || '卡券加载失败', icon: 'none' })
  } finally {
    loading.value = false
    loginChecked.value = true
  }
}

function switchStatus(status) {
  activeStatus.value = status
}

function goBuy() {
  uni.switchTab({ url: '/pages/category/index' })
}

onShow(loadCoupons)

onPullDownRefresh(async () => {
  try {
    await loadCoupons()
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
          :key="tab.key"
          class="tab"
          :class="{ active: activeStatus === tab.key }"
          @tap="switchStatus(tab.key)"
        >
          {{ tab.label }}
        </view>
      </view>
    </scroll-view>

    <view v-if="loading && !coupons.length" class="empty">正在加载卡券...</view>
    <view v-else-if="loginChecked && !filteredCoupons.length" class="empty">
      <view class="empty-icon">🎫</view>
      <view>暂无{{ tabs.find((t) => t.key === activeStatus)?.label }}的卡券</view>
      <button class="go-buy" @tap="goBuy">去逛逛</button>
    </view>

    <view
      v-for="coupon in filteredCoupons"
      :key="coupon.id"
      class="coupon-card"
      :class="{ dim: coupon.status !== 'unused', reissue: isReissueCoupon(coupon) }"
    >
      <view class="coupon-left" :class="{ reissue: isReissueCoupon(coupon) }">
        <template v-if="isReissueCoupon(coupon)">
          <view class="reissue-icon">🎁</view>
          <view class="cond">补送券</view>
        </template>
        <template v-else>
          <view class="face"><text class="unit">¥</text><text class="amount">{{ money(coupon.amount) }}</text></view>
          <view class="cond">{{ Number(coupon.min_spend) > 0 ? `满${money(coupon.min_spend)}可用` : '无门槛' }}</view>
        </template>
      </view>
      <view class="coupon-right">
        <view class="name">{{ coupon.name }}</view>
        <view v-if="isReissueCoupon(coupon)" class="reissue-sub">{{ coupon.description || '随单免费补配，可与优惠券叠加' }}</view>
        <view class="expire">有效期至 {{ dateTimeSec(coupon.expires_at) }}</view>
        <view class="status-tag" :class="coupon.status">{{ statusLabel(coupon.status) }}</view>
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
  padding: 14rpx 30rpx;
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
  margin-bottom: 18rpx;
  font-size: 88rpx;
}

.go-buy {
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

.go-buy::after { border: none; }

.coupon-card {
  display: flex;
  align-items: stretch;
  margin-bottom: 22rpx;
  border-radius: 24rpx;
  overflow: hidden;
  background: #fff;
}

.coupon-card.dim {
  opacity: .6;
}

.coupon-left {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
  width: 232rpx;
  padding: 34rpx 16rpx;
  color: #fff;
  background: linear-gradient(135deg, #ff7a45, #f20d2f);
}

.face {
  display: flex;
  align-items: baseline;
}

.unit { font-size: 30rpx; font-weight: 800; }
.amount { font-size: 68rpx; font-weight: 900; }
.cond { color: #fff; font-size: 23rpx; opacity: .95; }

/* 补送券左侧用绿色区分满减券的红色，图标替代金额面额 */
.coupon-left.reissue { background: linear-gradient(135deg, #5bb84f, #2f6b23); }
.reissue-icon { font-size: 60rpx; line-height: 1; }
.reissue-sub { color: #2f6b23; font-size: 24rpx; font-weight: 700; }

.coupon-right {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 12rpx;
  padding: 30rpx 28rpx;
}

.name {
  color: #222;
  font-size: 31rpx;
  font-weight: 900;
}

.expire {
  color: #999;
  font-size: 24rpx;
}

.status-tag {
  align-self: flex-start;
  padding: 4rpx 16rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  font-weight: 700;
  color: #2f6b23;
  background: #eef7e6;
}

.status-tag.used,
.status-tag.expired {
  color: #999;
  background: #f0f0f0;
}
</style>
