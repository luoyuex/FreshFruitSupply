<script setup>
import { computed, getCurrentInstance, nextTick, onMounted, onUnmounted, shallowRef, watch } from 'vue'

// 认证活动海报弹窗 —— 首页自动弹出，关闭后 3 天内不再出现
// 已认证用户不弹；未登录用户也可弹
//
// 海报是竖长图，宽度铺满时高度会很长，矮宽屏（平板、横屏、分屏）上按钮会被顶出屏幕，
// 固定小宽度又会让大屏显得空，所以卡片宽度按「宽度和高度哪个先到极限」反算。
// 另外项目用的是自定义 tabBar（fixed 在页面底部、z-index 更高），windowHeight 把它也算在里面，
// 所以 tab 页必须在底部给它和 home 指示条留出空间，否则按钮会被 tab 栏盖住。

const props = defineProps({
  visible: { type: Boolean, default: false },
  // 海报图片路径，可以是 /static/xxx.png 或远程 https:// 地址
  posterSrc: { type: String, default: '' },
})

const emit = defineEmits(['close', 'goVerify'])

const instance = getCurrentInstance()

const CARD_MIN_WIDTH_RPX = 420 // 卡片最小宽度，再窄就交给遮罩滚动兜底
const MASK_PADDING_X_RPX = 40 // 遮罩左右内边距，与样式保持一致
const MASK_PADDING_Y_RPX = 60 // 遮罩上下内边距，与样式保持一致
const TAB_BAR_HEIGHT_RPX = 110 // 自定义 tabBar 高度，与 custom-tab-bar/index.wxss 保持一致
const BOTTOM_GAP_RPX = 20 // 卡片与底部障碍物之间的额外留白
const ACTIONS_FALLBACK_RPX = 260 // 按钮区高度兜底值（首次渲染还没量到真实高度时用）
const FALLBACK_RATIO = 1.5 // 取不到图片尺寸时的兜底高宽比

const systemBox = shallowRef({ width: 0, height: 0 }) // systemInfo 结果，仅作首次渲染的起点
const measuredBox = shallowRef(null) // 遮罩真实渲染尺寸，量到后以它为准
const measuredActions = shallowRef(0) // 按钮区真实高度
const safeBottomInset = shallowRef(0) // home 指示条高度（px）
const hasTabBar = shallowRef(false)
const posterRatio = shallowRef(FALLBACK_RATIO) // 高 / 宽

const viewportBox = computed(() => measuredBox.value || systemBox.value)

// 自定义 tabBar 只挂在 tab 页上
function detectTabBar() {
  // #ifdef MP-WEIXIN
  const pages = getCurrentPages()
  const current = pages[pages.length - 1]
  if (current && typeof current.getTabBar === 'function' && current.getTabBar()) return true
  // #endif
  return false
}

function syncEnv() {
  const info = uni.getSystemInfoSync()
  systemBox.value = { width: info.windowWidth, height: info.windowHeight }
  safeBottomInset.value = info.safeArea ? Math.max(info.screenHeight - info.safeArea.bottom, 0) : 0
  hasTabBar.value = detectTabBar()
}

// 遮罩上下内边距：底部要给 tabBar 和安全区让位
const maskPadding = computed(() => {
  const base = uni.upx2px(MASK_PADDING_Y_RPX)
  const bottom = hasTabBar.value
    ? Math.max(base, uni.upx2px(TAB_BAR_HEIGHT_RPX) + safeBottomInset.value + uni.upx2px(BOTTOM_GAP_RPX))
    : base
  return { top: base, bottom }
})

// 读图片真实尺寸算高宽比，换海报后不用改代码
function syncPosterRatio() {
  if (!props.posterSrc) {
    posterRatio.value = FALLBACK_RATIO
    return
  }
  uni.getImageInfo({
    src: props.posterSrc,
    success: (res) => {
      if (res.width && res.height) posterRatio.value = res.height / res.width
    },
  })
}

// 量遮罩和按钮区的真实渲染尺寸，作为布局计算依据
function measure() {
  const query = uni.createSelectorQuery()
  if (instance) query.in(instance.proxy)
  query.select('.poster-mask').boundingClientRect()
  query.select('.poster-actions').boundingClientRect()
  query.exec((res) => {
    const [mask, actions] = res || []
    if (mask && mask.width) measuredBox.value = { width: mask.width, height: mask.height }
    if (actions && actions.height) measuredActions.value = actions.height
    // tabBar 实例要等页面渲染完才拿得到，这里再确认一次
    const tabBar = detectTabBar()
    if (tabBar !== hasTabBar.value) hasTabBar.value = tabBar
  })
}

const cardWidth = computed(() => {
  const { width, height } = viewportBox.value
  if (!width) return ''
  const widthLimit = width - uni.upx2px(MASK_PADDING_X_RPX) * 2
  const actionsHeight = measuredActions.value || uni.upx2px(ACTIONS_FALLBACK_RPX)
  const maxImageHeight = height - maskPadding.value.top - maskPadding.value.bottom - actionsHeight
  const heightLimit = maxImageHeight / posterRatio.value
  return `${Math.max(Math.min(widthLimit, heightLimit), uni.upx2px(CARD_MIN_WIDTH_RPX))}px`
})

function refresh() {
  syncEnv()
  if (props.visible) nextTick(measure)
}

syncEnv()
watch(() => props.posterSrc, syncPosterRatio, { immediate: true })

// 弹窗打开后再量一次，此时遮罩和按钮区才真正渲染出来
watch(
  () => props.visible,
  (open) => {
    if (open) refresh()
  },
)

onMounted(() => {
  if (props.visible) refresh()
  // 横竖屏切换、平板分屏时重新计算
  if (typeof uni.onWindowResize === 'function') uni.onWindowResize(refresh)
})

onUnmounted(() => {
  if (typeof uni.offWindowResize === 'function') uni.offWindowResize(refresh)
})

function onClose() {
  emit('close')
}

function onGoVerify() {
  emit('goVerify')
}
</script>

<template>
  <view
    v-if="visible"
    class="poster-mask"
    :style="{ paddingTop: maskPadding.top + 'px', paddingBottom: maskPadding.bottom + 'px' }"
    @tap="onClose"
  >
    <view class="poster-card" :style="posterSrc ? { width: cardWidth } : ''" @tap.stop>
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
          <text class="placeholder-desc">上传门店资料，完成认证后即可享受认证优惠价</text>
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
  overflow-y: auto;
  /* 上下内边距由 JS 按 tabBar / 安全区动态给，见 maskPadding */
  padding: 60rpx 40rpx;
  background: rgba(0, 0, 0, .55);
  box-sizing: border-box;
}

.poster-card {
  /* margin: auto 让卡片在 flex 容器里溢出时仍能被滚动到，不会被裁掉顶部 */
  margin: auto;
  flex-shrink: 0;
  width: 100%;
  max-width: 100%;
  display: flex;
  flex-direction: column;
  border-radius: 24rpx;
  background: #fff;
  overflow: hidden;
}

.poster-img-wrap {
  position: relative;
  width: 100%;
  flex-shrink: 0;
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
  flex-shrink: 0;
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
