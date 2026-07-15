<script setup>
import { computed, shallowRef } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { shortDateTime } from '../../utils/format.js'
import { request } from '../../utils/request.js'
import { hasCustomerLogin } from '../../utils/auth.js'

const items = shallowRef([])
const lastReadId = shallowRef(0)
const loading = shallowRef(false)
const loaded = shallowRef(false)

// 登录用户才有已读追踪：未读 = id 大于已读位；游客无红点
const loggedIn = computed(() => hasCustomerLogin())
const unreadCount = computed(() => (loggedIn.value ? items.value.filter((item) => item.id > lastReadId.value).length : 0))

function isUnread(item) {
  return loggedIn.value && item.id > lastReadId.value
}

async function loadAnnouncements() {
  loading.value = true
  try {
    const feed = await request({ url: '/announcements' })
    items.value = feed.items || []
    lastReadId.value = Number(feed.last_read_id || 0)
  } catch (err) {
    uni.showToast({ title: err.message || '公告加载失败', icon: 'none' })
  } finally {
    loading.value = false
    loaded.value = true
  }
}

function openDetail(item) {
  // 详情内容随列表已拉到，用 storage 传递，详情页无需再请求
  uni.setStorageSync('announcement_detail', JSON.stringify(item))
  uni.navigateTo({ url: `/pages/announcement/detail?id=${item.id}` })
}

async function markAllRead() {
  if (!loggedIn.value) {
    uni.showToast({ title: '登录后可标记已读', icon: 'none' })
    return
  }
  if (!unreadCount.value) return
  try {
    const res = await request({ url: '/announcements/read', method: 'POST' })
    lastReadId.value = Number(res.last_read_id || lastReadId.value)
    uni.showToast({ title: '已全部标为已读', icon: 'success' })
  } catch (err) {
    uni.showToast({ title: err.message || '操作失败', icon: 'none' })
  }
}

onShow(loadAnnouncements)

onPullDownRefresh(async () => {
  try {
    await loadAnnouncements()
  } finally {
    uni.stopPullDownRefresh()
  }
})
</script>

<template>
  <view class="page">
    <view v-if="loggedIn && unreadCount > 0" class="top-bar">
      <text class="unread-text">{{ unreadCount }} 条未读</text>
      <button class="read-all" @tap="markAllRead">全部已读</button>
    </view>

    <view v-if="loading && !items.length" class="empty">正在加载公告...</view>
    <view v-else-if="loaded && !items.length" class="empty">
      <image class="empty-icon" src="/static/icons/mail.svg" mode="aspectFit" />
      <view>暂无公告</view>
    </view>

    <view
      v-for="item in items"
      :key="item.id"
      class="announcement-card"
      @tap="openDetail(item)"
    >
      <view class="card-head">
        <view class="title-wrap">
          <view v-if="isUnread(item)" class="unread-dot"></view>
          <text class="title">{{ item.title }}</text>
        </view>
        <text class="arrow">›</text>
      </view>
      <text class="date">{{ shortDateTime(item.created_at) }}</text>
      <view class="content">{{ item.content }}</view>
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

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18rpx;
  padding: 20rpx 26rpx;
  border-radius: 20rpx;
  background: #fff;
}

.unread-text { color: #f20d2f; font-size: 27rpx; font-weight: 800; }

.read-all {
  height: 60rpx;
  line-height: 60rpx;
  padding: 0 26rpx;
  border-radius: 999rpx;
  color: #fff;
  background: #2f6b23;
  font-size: 25rpx;
  font-weight: 800;
}
.read-all::after { border: none; }

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
  width: 78rpx;
  height: 78rpx;
  margin-bottom: 18rpx;
  opacity: .5;
}

.announcement-card {
  margin-bottom: 20rpx;
  padding: 26rpx;
  border-radius: 22rpx;
  background: #fff;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.title-wrap {
  display: flex;
  align-items: center;
  gap: 14rpx;
  flex: 1;
  min-width: 0;
}

.unread-dot {
  flex-shrink: 0;
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: #f20d2f;
}

.title {
  flex: 1;
  min-width: 0;
  color: #222;
  font-size: 30rpx;
  font-weight: 900;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.arrow { flex-shrink: 0; color: #bbb; font-size: 36rpx; }

.date {
  display: block;
  margin-top: 12rpx;
  color: #999;
  font-size: 23rpx;
}

.content {
  margin-top: 14rpx;
  color: #666;
  font-size: 26rpx;
  line-height: 1.5;
  overflow: hidden;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}
</style>
