<script setup>
// 认证活动海报弹窗 —— 首页自动弹出，关闭后 3 天内不再出现
// 已认证用户不弹；未登录用户也可弹

defineProps({
  visible: { type: Boolean, default: false },
  // 海报图片路径，可以是 /static/xxx.png 或远程 https:// 地址
  posterSrc: { type: String, default: '' },
})

const emit = defineEmits(['close', 'goVerify'])

function onClose() {
  emit('close')
}

function onGoVerify() {
  emit('goVerify')
}
</script>

<template>
  <view v-if="visible" class="poster-mask" @tap="onClose">
    <view class="poster-card" @tap.stop>
      <view class="poster-img-wrap">
        <image
          v-if="posterSrc"
          class="poster-img"
          :src="posterSrc"
          mode="widthFix"
        />
        <view v-else class="poster-placeholder">
          <text class="placeholder-icon">🎉</text>
          <text class="placeholder-title">认证店铺享超低价</text>
          <text class="placeholder-desc">上传门店资料，审核通过后即可享受认证优惠价</text>
        </view>
        <view class="close-btn" @tap="onClose">✕</view>
      </view>
      <view class="poster-actions">
        <button class="action-verify" @tap="onGoVerify">去认证</button>
        <view class="action-dismiss" @tap="onClose">暂不需要</view>
      </view>
    </view>
  </view>
</template>

<style scoped>
.poster-mask {
  position: fixed;
  z-index: 100;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60rpx 40rpx;
  background: rgba(0, 0, 0, .55);
  box-sizing: border-box;
}

.poster-card {
  width: 100%;
  max-width: 600rpx;
  display: flex;
  flex-direction: column;
  border-radius: 24rpx;
  background: #fff;
  overflow: hidden;
}

.poster-img-wrap {
  position: relative;
  width: 100%;
}

.poster-img {
  width: 100%;
  display: block;
}

.poster-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80rpx 40rpx;
  background: linear-gradient(180deg, #ff5757, #ff7a45 52%, #ffe6dc);
}

.placeholder-icon {
  font-size: 80rpx;
}

.placeholder-title {
  margin-top: 20rpx;
  color: #fff;
  font-size: 36rpx;
  font-weight: 900;
}

.placeholder-desc {
  margin-top: 14rpx;
  color: rgba(255, 255, 255, .85);
  font-size: 26rpx;
  text-align: center;
  line-height: 1.5;
}

.close-btn {
  position: absolute;
  top: 16rpx;
  right: 16rpx;
  width: 52rpx;
  height: 52rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(0, 0, 0, .35);
  color: #fff;
  font-size: 28rpx;
  line-height: 1;
}

.poster-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18rpx;
  padding: 28rpx 32rpx 34rpx;
}

.action-verify {
  width: 100%;
  height: 84rpx;
  line-height: 84rpx;
  border-radius: 999rpx;
  color: #fff;
  background: linear-gradient(90deg, #ff315f, #ff7a22, #ffd34a);
  font-size: 30rpx;
  font-weight: 900;
}

.action-verify::after {
  border: none;
}

.action-dismiss {
  color: #999;
  font-size: 26rpx;
  padding: 8rpx 0;
}
</style>
