<script setup>
const sections = [
  {
    title: '一、服务说明',
    items: [
      '本小程序用于展示水果报价、提交预订订单、维护收货地址和提交店铺认证资料。',
      '平台展示的价格为预估报价，水果价格会受行情、等级、规格和库存影响，最终以供应商确认结果为准。',
      '当前订单不支持线上支付，提交订单后由供应商确认配送和结算方式。',
    ],
  },
  {
    title: '二、账号与资料',
    items: [
      '用户通过微信登录后可使用预订、地址管理、订单查看等功能。',
      '用户应保证填写的联系人、手机号、配送地址等信息真实、准确、完整。',
      '如因资料错误导致无法联系、配送延误或配送失败，需由用户自行承担相应影响。',
    ],
  },
  {
    title: '三、店铺认证',
    items: [
      '认证资料用于确认客户经营身份，包含店铺名称、联系人、手机号、经营类型和店铺图片。',
      '认证通过后可查看或使用认证价格；认证审核中或未通过时，仍以普通报价为准。',
      '如提交虚假、无关或侵犯他人权益的资料，供应商有权拒绝认证或取消已认证资格。',
    ],
  },
  {
    title: '四、订单规则',
    items: [
      '用户提交订单后，订单状态默认为待确认，供应商会根据库存、线路和配送安排进行处理。',
      '待确认或已确认订单可在每天22:30前修改；进入配送中、已完成、已取消后不可修改。',
      '如需临时调整订单，请尽早联系供应商，是否可调整以实际备货和配送情况为准。',
    ],
  },
  {
    title: '五、配送与验收',
    items: [
      '配送范围、配送时间和起订要求以供应商实际安排为准。',
      '水果属于生鲜商品，用户收到后应及时核对品类、数量、规格和外观。',
      '如发现明显质量或数量问题，请在收货后及时联系供应商并提供照片或视频说明。',
    ],
  },
  {
    title: '六、隐私与数据使用',
    items: [
      '平台仅收集完成登录、报价展示、订单配送、店铺认证所需的必要信息。',
      '收货地址、手机号、店铺图片等资料仅用于业务处理，不会用于无关用途。',
      '供应商会尽力保护用户资料安全，但用户也应妥善保管自己的微信账号和设备。',
    ],
  },
  {
    title: '七、协议更新',
    items: [
      '供应商可根据业务调整更新本协议内容，更新后将在小程序内展示。',
      '用户继续使用小程序功能，即视为已阅读并同意更新后的协议内容。',
    ],
  },
]
</script>

<template>
  <view class="page">
    <view class="hero">
      <image class="hero-icon" src="/static/icons/file-text.svg" mode="aspectFit" />
      <view>
        <view class="title">用户协议</view>
        <view class="sub">请在下单和提交认证前阅读以下内容</view>
      </view>
    </view>

    <view class="notice">
      本协议围绕水果报价、预订配送和店铺认证制定。若你不同意协议内容，请停止使用相关功能。
    </view>

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
