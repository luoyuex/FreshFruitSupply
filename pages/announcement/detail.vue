<script setup>
import { onLoad } from '@dcloudio/uni-app'
import { shallowRef } from 'vue'
import { shortDateTime } from '../../utils/format.js'
import { request } from '../../utils/request.js'

const announcement = shallowRef(null)
const loading = shallowRef(false)

// 优先用列表页写入 storage 的快照秒开；无快照（如直接进入）再按 id 拉取
onLoad(async (query) => {
  const id = Number(query?.id || 0)
  const cached = readCache(id)
  if (cached) {
    announcement.value = cached
    return
  }
  if (!id) return
  loading.value = true
  try {
    const feed = await request({ url: '/announcements' })
    const items = feed.items || []
    announcement.value = items.find((item) => Number(item.id) === id) || null
  } catch (err) {
    uni.showToast({ title: err.message || '公告加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
})

function readCache(id) {
  try {
    const cached = JSON.parse(uni.getStorageSync('announcement_detail') || 'null')
    if (cached && Number(cached.id) === id) return cached
  } catch (error) {
    // 忽略解析失败，走接口兜底
  }
  return null
}
</script>

<template>
  <view class="page">
    <view v-if="announcement" class="card">
      <view class="title">{{ announcement.title }}</view>
      <view class="date">{{ shortDateTime(announcement.created_at) }}</view>
      <view class="divider"></view>
      <view class="content">{{ announcement.content }}</view>
    </view>
    <view v-else-if="loading" class="empty">正在加载公告...</view>
    <view v-else class="empty">公告不存在或已下架</view>
  </view>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding: 24rpx;
  background: #f3f3f3;
  box-sizing: border-box;
}

.card {
  padding: 34rpx 30rpx;
  border-radius: 22rpx;
  background: #fff;
}

.title {
  color: #173b16;
  font-size: 36rpx;
  font-weight: 900;
  line-height: 1.4;
}

.date {
  margin-top: 16rpx;
  color: #9aa792;
  font-size: 24rpx;
}

.divider {
  margin: 26rpx 0;
  height: 1rpx;
  background: #eef0ea;
}

.content {
  color: #3f4a3b;
  font-size: 29rpx;
  line-height: 1.7;
  white-space: pre-wrap;
}

.empty {
  margin-top: 120rpx;
  text-align: center;
  color: #8a9784;
  font-size: 28rpx;
}
</style>
