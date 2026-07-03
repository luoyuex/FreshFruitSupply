<script setup>
import { computed, onMounted, shallowRef } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { request } from '../../../utils/request.js'
import { statusLabel } from '../../../utils/format.js'
import { goAdminNav, redirectIfNoPermission, visibleAdminNavItems } from '../../../utils/admin.js'

const verifications = shallowRef([])
const loading = shallowRef(false)
const reviewingId = shallowRef(null)
const navItems = computed(() => visibleAdminNavItems())

async function loadVerifications() {
  loading.value = true
  try {
    verifications.value = await request({ url: '/admin/verifications', admin: true })
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
  } finally {
    loading.value = false
  }
}

async function review(item, status) {
  uni.showModal({
    title: status === 'verified' ? '通过认证' : '拒绝认证',
    content: `确认将“${item.shop_name}”改为${statusLabel(status)}？`,
    success: async (res) => {
      if (!res.confirm) return
      reviewingId.value = item.id
      try {
        const updated = await request({ url: `/admin/verifications/${item.id}`, method: 'PATCH', admin: true, data: { status } })
        verifications.value = verifications.value.map((verification) => verification.id === item.id ? updated : verification)
        await loadVerifications()
        uni.showToast({ title: '审核已更新', icon: 'success' })
      } catch (err) {
        uni.showToast({ title: err.message, icon: 'none' })
      } finally {
        reviewingId.value = null
      }
    },
  })
}

function preview(urls, current) {
  uni.previewImage({ urls, current })
}

function guardedLoadVerifications() {
  if (redirectIfNoPermission('verifications')) return
  loadVerifications()
}

onMounted(guardedLoadVerifications)
onShow(guardedLoadVerifications)

onPullDownRefresh(async () => {
  try {
    await loadVerifications()
  } finally {
    uni.stopPullDownRefresh()
  }
})
</script>

<template>
  <view class="page">
    <view class="admin-nav">
      <button v-for="item in navItems" :key="item.key" class="nav-button" :class="{ active: item.key === 'verifications' }" @tap="goAdminNav(item)">{{ item.label }}</button>
    </view>
    <view v-if="loading" class="empty">正在加载认证申请...</view>
    <view v-for="item in verifications" :key="item.id" class="card">
      <view class="head">
        <text class="shop">{{ item.shop_name }}</text>
        <text class="status">{{ statusLabel(item.status) }}</text>
      </view>
      <view class="info">{{ item.contact_name }} · {{ item.phone }} · {{ item.business_type }}</view>
      <view class="images">
        <image v-for="url in item.image_urls" :key="url" class="image" :src="url" mode="aspectFill" @tap="preview(item.image_urls, url)" />
      </view>
      <view class="actions">
        <button class="pass" :loading="reviewingId === item.id" :disabled="reviewingId === item.id || item.status === 'verified'" @tap="review(item, 'verified')">通过</button>
        <button class="reject" :loading="reviewingId === item.id" :disabled="reviewingId === item.id || item.status === 'rejected'" @tap="review(item, 'rejected')">拒绝</button>
      </view>
    </view>
  </view>
</template>

<style scoped>
.page { min-height: 100vh; padding: 24rpx; background: #f5f8ef; box-sizing: border-box; }
.admin-nav { display: flex; gap: 10rpx; margin-bottom: 20rpx; }
.nav-button { flex: 1; height: 70rpx; line-height: 70rpx; border-radius: 999rpx; color: #2f4b21; background: #fff; font-size: 24rpx; }
.nav-button.active { color: #fff; background: #2f6b23; }
.card, .empty { margin-top: 18rpx; padding: 24rpx; border-radius: 26rpx; background: #fff; box-shadow: 0 10rpx 26rpx rgba(73,83,47,.08); }
.head { display: flex; justify-content: space-between; }
.shop { font-size: 31rpx; font-weight: 900; color: #173b16; }
.status { color: #df5d00; font-weight: 900; }
.info { margin-top: 12rpx; color: #60715c; font-size: 25rpx; }
.images { display: flex; gap: 12rpx; margin-top: 16rpx; }
.image { width: 160rpx; height: 160rpx; border-radius: 18rpx; background: #eef5e8; }
.actions { display: flex; gap: 14rpx; margin-top: 18rpx; }
.pass, .reject { flex: 1; height: 70rpx; line-height: 70rpx; border-radius: 999rpx; color: #fff; font-size: 26rpx; }
.pass { background: #2f6b23; }
.reject { background: #9a3412; }
</style>
