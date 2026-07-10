<script setup>
import { onMounted, shallowRef } from 'vue'

// 可拖动的浮动购物车悬浮球。放在 components/float-cart 下，uni-app easycom 会自动引入，
// 页面里直接写 <float-cart :count="cartTotal" /> 即可，无需 import。
const props = defineProps({
  // 角标数量，为 0 时整个悬浮球隐藏
  count: { type: Number, default: 0 },
  // 初始位置：距屏幕右侧、底部的边距（px）
  right: { type: Number, default: 28 },
  bottom: { type: Number, default: 136 },
})

const emit = defineEmits(['tap'])

const SIZE_RPX = 92 // 悬浮球直径（rpx）

const cartX = shallowRef(0)
const cartY = shallowRef(0)
const isDragging = shallowRef(false)
const startX = shallowRef(0)
const startY = shallowRef(0)
const moveStartX = shallowRef(0)
const moveStartY = shallowRef(0)
const hasMoved = shallowRef(false)

function cartSizePx() {
  return SIZE_RPX / 750 * uni.getSystemInfoSync().windowWidth
}

function initCartPosition() {
  const sysInfo = uni.getSystemInfoSync()
  const size = cartSizePx()
  cartX.value = sysInfo.windowWidth - size - props.right
  cartY.value = sysInfo.windowHeight - props.bottom - size
}

function onCartTouchStart(e) {
  const touch = e.touches[0]
  startX.value = touch.clientX
  startY.value = touch.clientY
  moveStartX.value = cartX.value
  moveStartY.value = cartY.value
  isDragging.value = true
  hasMoved.value = false
}

function onCartTouchMove(e) {
  if (!isDragging.value) return
  const touch = e.touches[0]
  const dx = touch.clientX - startX.value
  const dy = touch.clientY - startY.value

  if (Math.abs(dx) > 5 || Math.abs(dy) > 5) {
    hasMoved.value = true
  }

  const sysInfo = uni.getSystemInfoSync()
  const size = cartSizePx()
  let newX = moveStartX.value + dx
  let newY = moveStartY.value + dy

  // 边界限制
  newX = Math.max(0, Math.min(newX, sysInfo.windowWidth - size))
  newY = Math.max(0, Math.min(newY, sysInfo.windowHeight - size))

  cartX.value = newX
  cartY.value = newY
}

function onCartTouchEnd() {
  isDragging.value = false
  // 没有拖动就当作点击。放在 touchend 里判断比单独绑 @tap 更可靠：
  // 小程序里 touch 事件带 .stop.prevent 会干扰 tap 手势识别，导致点击经常不触发。
  if (!hasMoved.value) handleTap()
}

function handleTap() {
  emit('tap')
  uni.switchTab({ url: '/pages/cart/index' })
}

onMounted(initCartPosition)
</script>

<template>
  <view
    v-if="count"
    class="float-cart"
    :style="{ left: cartX + 'px', top: cartY + 'px' }"
    @touchstart.stop.prevent="onCartTouchStart"
    @touchmove.stop.prevent="onCartTouchMove"
    @touchend.stop.prevent="onCartTouchEnd"
  >
    <text class="cart-icon">🛒</text>
    <text class="cart-badge">{{ count }}</text>
  </view>
</template>

<style scoped>
.float-cart {
  position: fixed;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 92rpx;
  height: 92rpx;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 8rpx 26rpx rgba(0, 0, 0, .12);
  z-index: 999;
}

.cart-icon {
  font-size: 42rpx;
}

.cart-badge {
  position: absolute;
  right: 4rpx;
  top: 0;
  min-width: 30rpx;
  height: 30rpx;
  line-height: 30rpx;
  border-radius: 999rpx;
  text-align: center;
  color: #fff;
  background: #f20d2f;
  font-size: 20rpx;
}
</style>
