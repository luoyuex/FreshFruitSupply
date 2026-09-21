<script setup>
import { computed } from 'vue'
import { flags } from '../../utils/flags.js'

// 认证功能开关：关闭时过滤掉认证相关章节与措辞，章节序号动态重排
const verificationOn = computed(() => flags.verification_enabled)

const CN_NUMS = ['一', '二', '三', '四', '五', '六', '七']

const sectionDefs = [
  {
    title: '服务说明',
    items: [
      '本小程序用于展示水果报价、提交订单和维护收货地址。',
      '平台展示的价格为预估报价，水果价格会受行情、等级、规格和库存影响，最终以商家确认结果为准。',
      '下单需完成微信支付，支付成功后由商家确认库存并安排配送。',
    ],
  },
  {
    title: '账号与资料',
    items: [
      '用户通过微信登录后可使用下单、地址管理、订单查看等功能。',
      '用户应保证填写的联系人、手机号、配送地址等信息真实、准确、完整。',
      '如因资料错误导致无法联系、配送延误或配送失败，需由用户自行承担相应影响。',
    ],
  },
  {
    title: '店铺认证',
    verification: true,
    items: [
      '认证资料用于确认客户经营身份，包含店铺名称、联系人、手机号、经营类型和店铺图片。',
      '认证通过后可查看或使用认证价格；认证审核中或未通过时，仍以普通报价为准。',
      '如提交虚假、无关或侵犯他人权益的资料，商家有权拒绝认证或取消已认证资格。',
    ],
  },
  {
    title: '订单规则',
    items: [
      '用户提交订单后，订单状态默认为待确认，商家会根据库存、线路和配送安排进行处理。',
      '待确认或已确认订单可在每天22:00前修改；进入配送中、已完成、已取消后不可修改。',
      '如需临时调整订单，请尽早联系商家，是否可调整以实际备货和配送情况为准。',
    ],
  },
  {
    title: '配送与验收',
    items: [
      '每天22:00前完成下单的订单，将于次日10:00前送达。',
      '配送范围以商家实际安排为准。',
      '水果属于生鲜商品，用户收到后应及时核对品类、数量、规格和外观。',
      '如发现明显质量或数量问题，请在收货后及时联系商家并提供照片或视频说明。',
    ],
  },
  {
    title: '隐私与数据使用',
    items: () => [
      verificationOn.value
        ? '平台仅收集完成登录、报价展示、订单配送、店铺认证所需的必要信息。'
        : '平台仅收集完成登录、报价展示、订单配送所需的必要信息。',
      '收货地址、手机号等资料仅用于业务处理，不会用于无关用途。',
      '商家会尽力保护用户资料安全，但用户也应妥善保管自己的微信账号和设备。',
    ],
  },
  {
    title: '协议更新',
    items: [
      '商家可根据业务调整更新本协议内容，更新后将在小程序内展示。',
      '用户继续使用小程序功能，即视为已阅读并同意更新后的协议内容。',
    ],
  },
]

const sections = computed(() =>
  sectionDefs
    .filter((section) => !section.verification || verificationOn.value)
    .map((section, index) => ({
      title: `${CN_NUMS[index]}、${section.title}`,
      items: typeof section.items === 'function' ? section.items() : section.items,
    })),
)

const heroSub = computed(() => (verificationOn.value ? '请在下单和提交认证前阅读以下内容' : '请在下单前阅读以下内容'))
const noticeText = computed(() =>
  verificationOn.value
    ? '本协议围绕水果报价、下单配送和店铺认证制定。若你不同意协议内容，请停止使用相关功能。'
    : '本协议围绕水果报价和下单配送制定。若你不同意协议内容，请停止使用相关功能。',
)
</script>

<template>
  <view class="page">
    <view class="hero">
      <image class="hero-icon" src="/static/icons/file-text.svg" mode="aspectFit" />
      <view>
        <view class="title">用户协议</view>
        <view class="sub">{{ heroSub }}</view>
      </view>
    </view>

    <view class="notice">{{ noticeText }}</view>

    <view v-for="section in sections" :key="section.title" class="section">
      <view class="section-title">{{ section.title }}</view>
      <view v-for="item in section.items" :key="item" class="item">{{ item }}</view>
    </view>

    <view class="footer">最后更新：2026年6月11日</view>
  </view>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding: 24rpx 24rpx 56rpx;
  background: #f3f3f3;
  box-sizing: border-box;
}

.hero {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 30rpx;
  border-radius: 28rpx;
  background: #fff;
}

.hero-icon {
  width: 64rpx;
  height: 64rpx;
}

.title {
  color: #333;
  font-size: 38rpx;
  font-weight: 900;
}

.sub {
  margin-top: 8rpx;
  color: #777;
  font-size: 25rpx;
}

.notice,
.section {
  margin-top: 18rpx;
  padding: 26rpx;
  border-radius: 24rpx;
  background: #fff;
}

.notice {
  color: #805200;
  background: #fff7df;
  font-size: 26rpx;
  line-height: 1.6;
}

.section-title {
  color: #333;
  font-size: 30rpx;
  font-weight: 900;
}

.item {
  position: relative;
  margin-top: 16rpx;
  padding-left: 24rpx;
  color: #666;
  font-size: 26rpx;
  line-height: 1.65;
}

.item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 18rpx;
  width: 8rpx;
  height: 8rpx;
  border-radius: 50%;
  background: #ffb700;
}

.footer {
  margin-top: 24rpx;
  text-align: center;
  color: #999;
  font-size: 24rpx;
}
</style>
