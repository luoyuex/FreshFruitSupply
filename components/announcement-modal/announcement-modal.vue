<script setup>
import { shortDateTime } from '../../utils/format.js'

// 公告弹窗：首页自动弹窗与「我的」页历史共用。放 components/ 下由 easycom 自动引入，
// 页面直接写 <announcement-modal :visible :items @close /> 即可，无需 import。
defineProps({
  visible: { type: Boolean, default: false },
  items: { type: Array, default: () => [] }, // 启用中的公告，最新在前
})

const emit = defineEmits(['close'])

function close() {
  emit('close')
}
</script>

<template>
  <view v-if="visible" class="modal-mask" @tap="close">
    <view class="modal-card" @tap.stop>
      <view class="modal-title">公告</view>
      <scroll-view scroll-y class="list">
        <view v-if="!items.length" class="empty">暂无公告</view>
        <view v-for="item in items" :key="item.id" class="item">
          <view class="item-head">
            <text class="item-title">{{ item.title }}</text>
            <text class="item-date">{{ shortDateTime(item.created_at) }}</text>
          </view>
          <view class="item-content">{{ item.content }}</view>
        </view>
      </scroll-view>
      <button class="close-btn" @tap="close">我知道了</button>
    </view>
  </view>
</template>

<style scoped>
.modal-mask {
  position: fixed;
  z-index: 95;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40rpx;
  background: rgba(0, 0, 0, .45);
  box-sizing: border-box;
}

.modal-card {
  width: 100%;
  max-height: 82vh;
  display: flex;
  flex-direction: column;
  padding: 34rpx 30rpx;
  border-radius: 28rpx;
  background: #fff;
  box-sizing: border-box;
}

.modal-title { color: #173b16; font-size: 34rpx; font-weight: 900; text-align: center; }

.list { max-height: 60vh; margin-top: 24rpx; }

.empty { padding: 60rpx 0; text-align: center; color: #8a9784; font-size: 26rpx; }

.item {
  padding: 24rpx 22rpx;
  border-radius: 18rpx;
  background: #f7f9f3;
}

.item + .item { margin-top: 18rpx; }

.item-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16rpx;
}

.item-title { flex: 1; min-width: 0; color: #173b16; font-size: 30rpx; font-weight: 800; }
.item-date { flex-shrink: 0; color: #9aa792; font-size: 22rpx; }

.item-content {
  margin-top: 14rpx;
  color: #4a5646;
  font-size: 27rpx;
  line-height: 1.6;
  white-space: pre-wrap;
}

.close-btn {
  height: 84rpx;
  line-height: 84rpx;
  margin-top: 26rpx;
  border-radius: 16rpx;
  color: #fff;
  background: #2f6b23;
  font-size: 28rpx;
  font-weight: 800;
}
.close-btn::after { border: none; }
</style>
