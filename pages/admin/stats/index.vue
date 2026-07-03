<script setup>
import { computed, onMounted, shallowRef } from 'vue'
import { onPullDownRefresh } from '@dcloudio/uni-app'
import { money, statusLabel } from '../../../utils/format.js'
import { request } from '../../../utils/request.js'
import { goAdminNav, redirectIfNoPermission, visibleAdminNavItems } from '../../../utils/admin.js'

const loading = shallowRef(false)
const dateValue = shallowRef(todayText())
const stats = shallowRef(null)

const topItems = computed(() => stats.value?.items || [])
const statusRows = computed(() => stats.value?.statuses || [])
const navItems = computed(() => visibleAdminNavItems())

function todayText() {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

async function loadStats() {
  loading.value = true
  try {
    stats.value = await request({ url: `/admin/sales-stats?date=${dateValue.value}`, admin: true })
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
    if (err.message.includes('token') || err.message.includes('Missing')) {
      uni.redirectTo({ url: '/pages/admin/login/index' })
    }
  } finally {
    loading.value = false
  }
}

function changeDate(event) {
  dateValue.value = event.detail.value
  loadStats()
}

onMounted(() => {
  if (redirectIfNoPermission('stats')) return
  loadStats()
})

onPullDownRefresh(async () => {
  try {
    await loadStats()
  } finally {
    uni.stopPullDownRefresh()
  }
})
</script>

<template>
  <view class="page">
    <view class="admin-nav">
      <button v-for="item in navItems" :key="item.key" class="nav-button" :class="{ active: item.key === 'stats' }" @tap="goAdminNav(item)">{{ item.label }}</button>
    </view>

    <view class="date-card">
      <view>
        <view class="date-title">销售统计</view>
        <view class="date-sub">按非取消订单统计预估销售</view>
      </view>
      <picker mode="date" :value="dateValue" @change="changeDate">
        <view class="date-picker">{{ dateValue }}</view>
      </picker>
    </view>

    <view v-if="loading" class="empty">正在加载统计...</view>

    <view v-if="stats" class="summary-grid">
      <view class="summary-card">
        <text class="summary-label">订单数</text>
        <text class="summary-value">{{ stats.order_count }}</text>
      </view>
      <view class="summary-card">
        <text class="summary-label">商品种类</text>
        <text class="summary-value">{{ stats.item_kind_count }}</text>
      </view>
      <view class="summary-card">
        <text class="summary-label">总数量</text>
        <text class="summary-value">{{ stats.total_quantity }}</text>
      </view>
      <view class="summary-card hot">
        <text class="summary-label">预估金额</text>
        <text class="summary-value">¥{{ money(stats.estimated_total) }}</text>
      </view>
    </view>

    <view class="section-card">
      <view class="section-title">商品销售明细</view>
      <view v-if="!topItems.length" class="empty slim">当天暂无销售数据</view>
      <view v-for="item in topItems" :key="`${item.fruit_id}-${item.spec}-${item.unit}`" class="item-row">
        <view class="item-main">
          <view class="item-name">{{ item.fruit_name }}</view>
          <view class="item-sub">{{ item.spec }} · {{ item.order_count }}单</view>
        </view>
        <view class="item-stat">
          <view>{{ item.quantity }}{{ item.unit }}</view>
          <view class="amount">¥{{ money(item.subtotal) }}</view>
        </view>
      </view>
    </view>

    <view class="section-card">
      <view class="section-title">订单状态分布</view>
      <view v-if="!statusRows.length" class="empty slim">暂无订单</view>
      <view v-for="row in statusRows" :key="row.status" class="status-row">
        <text>{{ statusLabel(row.status) }}</text>
        <text>{{ row.order_count }}单 · ¥{{ money(row.amount) }}</text>
      </view>
    </view>
  </view>
</template>

<style scoped>
.page { min-height: 100vh; padding: 24rpx; background: #f5f8ef; box-sizing: border-box; }
.admin-nav { display: flex; gap: 10rpx; margin-bottom: 20rpx; }
.nav-button { flex: 1; height: 68rpx; line-height: 68rpx; border-radius: 999rpx; color: #2f4b21; background: #fff; font-size: 24rpx; }
.nav-button.active { color: #fff; background: #2f6b23; }
.date-card, .section-card, .empty { margin-top: 18rpx; padding: 24rpx; border-radius: 26rpx; background: #fff; box-shadow: 0 10rpx 26rpx rgba(73,83,47,.08); }
.date-card { display: flex; align-items: center; justify-content: space-between; gap: 20rpx; }
.date-title { color: #173b16; font-size: 34rpx; font-weight: 900; }
.date-sub { margin-top: 8rpx; color: #60715c; font-size: 24rpx; }
.date-picker { padding: 16rpx 24rpx; border-radius: 999rpx; color: #fff; background: #ef7d00; font-size: 25rpx; }
.summary-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16rpx; margin-top: 18rpx; }
.summary-card { padding: 26rpx; border-radius: 24rpx; background: #fff; box-shadow: 0 10rpx 26rpx rgba(73,83,47,.08); }
.summary-card.hot { background: #fff3d2; }
.summary-label { display: block; color: #60715c; font-size: 24rpx; }
.summary-value { display: block; margin-top: 12rpx; color: #173b16; font-size: 40rpx; font-weight: 900; }
.section-title { color: #173b16; font-size: 31rpx; font-weight: 900; }
.item-row, .status-row { display: flex; align-items: center; justify-content: space-between; gap: 18rpx; padding: 20rpx 0; border-bottom: 1rpx solid #edf2e6; }
.item-row:last-child, .status-row:last-child { border-bottom: 0; }
.item-main { flex: 1; min-width: 0; }
.item-name { color: #173b16; font-size: 28rpx; font-weight: 900; }
.item-sub { margin-top: 8rpx; color: #60715c; font-size: 24rpx; }
.item-stat { text-align: right; color: #48613b; font-size: 25rpx; font-weight: 800; }
.amount { margin-top: 8rpx; color: #df5d00; }
.status-row { color: #48613b; font-size: 26rpx; }
.empty { text-align: center; color: #768273; font-size: 26rpx; }
.empty.slim { padding: 44rpx 20rpx; box-shadow: none; }
</style>
