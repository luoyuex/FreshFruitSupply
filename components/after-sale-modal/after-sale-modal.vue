<script setup>
// 售后客服弹窗 —— 已完成订单点击"售后"按钮弹出
// 展示售后说明 + 微信二维码，引导客户添加客服微信
defineProps({
  visible: { type: Boolean, default: false },
})

const emit = defineEmits(['close'])

function onClose() {
  emit('close')
}

// 点击二维码 → 图片预览 → 长按弹出微信原生菜单 → "识别图中二维码"直达微信
function previewQrcode() {
  uni.previewImage({
    urls: ['/static/after-sale/qrcode.png'],
    current: '/static/after-sale/qrcode.png',
  })
}
</script>

<template>
  <view v-if="visible" class="modal-mask" @tap="onClose">
    <view class="modal-card" @tap.stop>
      <!-- 头部 -->
      <view class="card-head">
        <text class="head-icon">🛎️</text>
        <text class="head-title">售后客服</text>
        <text class="head-sub">如有商品问题，请联系我们</text>
      </view>

      <!-- 售后说明 -->
      <view class="info-section">
        <text class="info-tag">质量问题</text>
        <text class="info-tag">缺斤少两</text>
        <text class="info-tag">错发漏发</text>
        <text class="info-tag">其他问题</text>
      </view>

      <!-- 二维码 -->
      <view class="contact-section">
        <view class="qrcode-wrap" @tap="previewQrcode">
          <image
            class="qrcode-img"
            src="/static/after-sale/qrcode.png"
            mode="aspectFit"
          />
          <view class="qrcode-scan-hint">点击图片后长按 → 识别图中二维码</view>
        </view>
        <view class="contact-tip">打开微信扫一扫，添加客服微信</view>
      </view>

      <view class="card-foot">
        <text class="foot-text">工作时间：每天 9:00 - 18:00</text>
      </view>
    </view>
  </view>
</template>

<style scoped>
.modal-mask {
  position: fixed;
  z-index: 100;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40rpx;
  background: rgba(0, 0, 0, .5);
  box-sizing: border-box;
}

.modal-card {
  width: 100%;
  max-width: 620rpx;
  max-height: 88vh;
  overflow-y: auto;
  border-radius: 28rpx;
  background: #fff;
}

.card-head {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48rpx 30rpx 36rpx;
  background: linear-gradient(180deg, #ffb700, #ffa200);
  border-radius: 28rpx 28rpx 0 0;
}

.head-icon {
  font-size: 64rpx;
}

.head-title {
  margin-top: 12rpx;
  color: #fff;
  font-size: 38rpx;
  font-weight: 900;
}

.head-sub {
  margin-top: 8rpx;
  color: rgba(255, 255, 255, .85);
  font-size: 25rpx;
}

.info-section {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 16rpx;
  padding: 24rpx 32rpx 0;
}

.info-tag {
  padding: 8rpx 24rpx;
  border-radius: 999rpx;
  color: #8b6914;
  background: #fff8e7;
  font-size: 23rpx;
  font-weight: 600;
}

.contact-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32rpx 48rpx 24rpx;
}

.qrcode-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20rpx;
  border-radius: 20rpx;
  background: #f8f8f8;
}

.qrcode-img {
  width: 360rpx;
  height: 360rpx;
  border-radius: 12rpx;
  background: #fff;
}

.qrcode-scan-hint {
  margin-top: 14rpx;
  color: #aaa;
  font-size: 23rpx;
}

.contact-tip {
  margin-top: 20rpx;
  color: #666;
  font-size: 26rpx;
}

.card-foot {
  padding: 20rpx 32rpx 32rpx;
  text-align: center;
}

.foot-text {
  color: #bbb;
  font-size: 22rpx;
}
</style>
