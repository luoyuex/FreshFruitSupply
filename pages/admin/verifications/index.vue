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

async function revoke(item) {
  uni.showModal({
    title: '取消认证',
    content: `确认取消“${item.shop_name}”的认证资格？取消后客户将恢复普通价格，并可重新提交认证。`,
    confirmText: '取消认证',
    confirmColor: '#b42318',
    success: async (res) => {
      if (!res.confirm) return
      reviewingId.value = item.id
      try {
        const updated = await request({ url: `/admin/verifications/${item.id}`, method: 'PATCH', admin: true, data: { status: 'revoked', review_note: '认证资料需要重新提交' } })
        verifications.value = verifications.value.map((verification) => verification.id === item.id ? updated : verification)
        await loadVerifications()
        uni.showToast({ title: '认证已取消', icon: 'success' })
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
    <view v-if="loading" class="empty">正在加载认证记录...</view>
    <view v-else-if="!verifications.length" class="empty">暂无认证记录</view>
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
        <button v-if="item.status === 'verified'" class="revoke" :loading="reviewingId === item.id" :disabled="reviewingId === item.id" @tap="revoke(item)">取消认证</button>
        <view v-else class="inactive-hint">客户可重新提交认证</view>
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
.revoke { width: 220rpx; height: 70rpx; line-height: 70rpx; border-radius: 999rpx; color: #fff; background: #9a3412; font-size: 26rpx; }
.revoke::after { border: none; }
.inactive-hint { color: #7b8975; font-size: 24rpx; }
</style>
