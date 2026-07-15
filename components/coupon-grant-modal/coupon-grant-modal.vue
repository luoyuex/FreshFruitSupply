<script setup>
import { computed, shallowRef, watch } from 'vue'
import { money } from '../../utils/format.js'

// 后台「发券给指定用户」弹窗。放在 components/coupon-grant-modal 下，easycom 自动引入，
// 页面里直接写 <coupon-grant-modal ... /> 即可，无需 import。
// 两种形态：传入 customer 时客户固定（用户页单人补偿）；不传时展示客户搜索列表（卡券页）。
const props = defineProps({
  visible: { type: Boolean, default: false },
  templates: { type: Array, default: () => [] }, // 启用中的券种
  customers: { type: Array, default: () => [] }, // 选客户模式的候选客户
  customer: { type: Object, default: null }, // 固定客户；传入则隐藏选客户区
  saving: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'confirm'])

const selectedTemplateId = shallowRef(null)
const selectedCustomerId = shallowRef(null)
const keyword = shallowRef('')

const isFixedCustomer = computed(() => Boolean(props.customer))
const effectiveCustomerId = computed(() => (props.customer ? props.customer.id : selectedCustomerId.value))

function customerName(customer) {
  return customer?.nickname || customer?.shop_name || customer?.phone || '未命名客户'
}

const title = computed(() => (isFixedCustomer.value ? `发券给 ${customerName(props.customer)}` : '发券给用户'))

const filteredCustomers = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return props.customers
  return props.customers.filter((c) =>
    [c.phone, c.nickname, c.shop_name, c.contact_name]
      .filter(Boolean)
      .some((field) => String(field).toLowerCase().includes(kw)),
  )
})

// 每次打开重置选择，避免残留上一次的选中态
watch(
  () => props.visible,
  (open) => {
    if (open) {
      selectedTemplateId.value = null
      selectedCustomerId.value = null
      keyword.value = ''
    }
  },
)

function pickTemplate(id) {
  selectedTemplateId.value = id
}

function pickCustomer(id) {
  selectedCustomerId.value = id
}

function close() {
  emit('close')
}

function confirm() {
  if (!selectedTemplateId.value) {
    uni.showToast({ title: '请选择券种', icon: 'none' })
    return
  }
  const customerId = effectiveCustomerId.value
  if (!customerId) {
    uni.showToast({ title: '请选择客户', icon: 'none' })
    return
  }
  emit('confirm', { customerId, templateId: selectedTemplateId.value })
}
</script>

<template>
  <view v-if="visible" class="modal-mask" @tap="close">
    <view class="modal-card" @tap.stop>
      <view class="modal-title">{{ title }}</view>

      <template v-if="!isFixedCustomer">
        <view class="section-label">选择客户</view>
        <input v-model="keyword" class="search" placeholder="搜索手机号 / 昵称 / 店名 / 联系人" />
        <scroll-view scroll-y class="pick-list">
          <view v-if="!filteredCustomers.length" class="hint">没有匹配的客户</view>
          <view
            v-for="c in filteredCustomers"
            :key="c.id"
            class="pick-row"
            :class="{ on: selectedCustomerId === c.id }"
            @tap="pickCustomer(c.id)"
          >
            <view class="pick-main">
              <view class="pick-name">{{ customerName(c) }}</view>
              <view class="pick-sub">{{ c.phone }}<text v-if="c.shop_name"> · {{ c.shop_name }}</text></view>
            </view>
            <text class="tick">{{ selectedCustomerId === c.id ? '✓' : '' }}</text>
          </view>
        </scroll-view>
      </template>
      <view v-else class="fixed-customer">发放对象：{{ customerName(customer) }}（{{ customer.phone }}）</view>

      <view class="section-label">选择券种</view>
      <view v-if="!templates.length" class="hint">还没有启用中的券种，请先到卡券页创建。</view>
      <scroll-view v-else scroll-y class="pick-list">
        <view
          v-for="t in templates"
          :key="t.id"
          class="pick-row"
          :class="{ on: selectedTemplateId === t.id }"
          @tap="pickTemplate(t.id)"
        >
          <view class="pick-main">
            <view class="pick-name">
              <text>{{ t.name }}</text>
              <text v-if="t.kind === 'reissue'" class="kind-tag">补送券</text>
            </view>
            <view v-if="t.kind === 'reissue'" class="pick-sub">随单免费补配 · 有效期{{ t.valid_days }}天</view>
            <view v-else class="pick-sub">¥{{ money(t.amount) }} · {{ Number(t.min_spend) > 0 ? `满${money(t.min_spend)}可用` : '无门槛' }} · 有效期{{ t.valid_days }}天</view>
          </view>
          <text class="tick">{{ selectedTemplateId === t.id ? '✓' : '' }}</text>
        </view>
      </scroll-view>

      <view class="modal-actions">
        <button class="cancel" @tap="close">取消</button>
        <button class="save" :loading="saving" :disabled="saving" @tap="confirm">确认发放</button>
      </view>
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
  max-height: 84vh;
  overflow-y: auto;
  padding: 34rpx 30rpx;
  border-radius: 28rpx;
  background: #fff;
  box-sizing: border-box;
}

.modal-title { color: #173b16; font-size: 34rpx; font-weight: 900; text-align: center; }

.section-label { margin-top: 26rpx; color: #445; font-size: 25rpx; font-weight: 700; }

.search {
  width: 100%;
  height: 74rpx;
  margin-top: 14rpx;
  padding: 0 22rpx;
  border-radius: 16rpx;
  color: #222;
  background: #f4f6f0;
  box-sizing: border-box;
  font-size: 26rpx;
}

.fixed-customer {
  margin-top: 14rpx;
  padding: 20rpx 22rpx;
  border-radius: 16rpx;
  color: #2f4b21;
  background: #eef7e6;
  font-size: 26rpx;
  font-weight: 700;
}

.pick-list { max-height: 320rpx; margin-top: 14rpx; }

.hint { padding: 22rpx; color: #8a9784; font-size: 25rpx; text-align: center; }

.pick-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  margin-top: 12rpx;
  padding: 20rpx 22rpx;
  border: 2rpx solid #eef0ea;
  border-radius: 16rpx;
  background: #fafcf7;
}

.pick-row.on { border-color: #2f6b23; background: #eef7e6; }

.pick-main { flex: 1; min-width: 0; }
.pick-name { display: flex; align-items: center; gap: 12rpx; color: #173b16; font-size: 28rpx; font-weight: 800; }
.kind-tag { padding: 2rpx 12rpx; border-radius: 999rpx; color: #b45309; background: #fef0d8; font-size: 20rpx; font-weight: 800; }
.pick-sub { margin-top: 6rpx; color: #60715c; font-size: 23rpx; }
.tick { flex-shrink: 0; color: #2f6b23; font-size: 32rpx; font-weight: 900; }

.modal-actions { display: flex; gap: 16rpx; margin-top: 32rpx; }
.cancel, .save { flex: 1; height: 82rpx; line-height: 82rpx; border-radius: 16rpx; font-size: 28rpx; font-weight: 800; }
.cancel { color: #555; background: #eef0ea; }
.save { color: #fff; background: #2f6b23; }
.cancel::after, .save::after { border: none; }
</style>
