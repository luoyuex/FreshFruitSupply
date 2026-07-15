<script setup>
import { computed, onMounted, reactive, shallowRef } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { request } from '../../../utils/request.js'
import { money } from '../../../utils/format.js'
import { goAdminNav, redirectIfNoPermission, visibleAdminNavItems } from '../../../utils/admin.js'

const templates = shallowRef([])
const loading = shallowRef(false)
const saving = shallowRef(false)
const modalVisible = shallowRef(false)
const editingId = shallowRef(null)
const navItems = computed(() => visibleAdminNavItems())

// 发券给指定用户（补偿）
const grantVisible = shallowRef(false)
const granting = shallowRef(false)
const customers = shallowRef([])
const activeTemplates = computed(() => templates.value.filter((item) => item.is_active))

const form = reactive({
  name: '',
  kind: 'discount', // discount=满减券；reissue=商品补送券（无金额/门槛）
  amount: '',
  minSpend: '',
  validDays: '30',
  grantOnVerified: false,
  isActive: true,
  description: '',
})

const isReissueForm = computed(() => form.kind === 'reissue')

async function loadTemplates() {
  loading.value = true
  try {
    templates.value = await request({ url: '/admin/coupon-templates', admin: true })
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  form.name = ''
  form.kind = 'discount'
  form.amount = ''
  form.minSpend = ''
  form.validDays = '30'
  form.grantOnVerified = false
  form.isActive = true
  form.description = ''
  modalVisible.value = true
}

function openEdit(template) {
  editingId.value = template.id
  form.name = template.name
  form.kind = template.kind || 'discount'
  form.amount = String(template.amount)
  form.minSpend = String(template.min_spend)
  form.validDays = String(template.valid_days)
  form.grantOnVerified = template.grant_on_verified
  form.isActive = template.is_active
  form.description = template.description || ''
  modalVisible.value = true
}

function closeModal() {
  modalVisible.value = false
}

function validate() {
  if (!form.name.trim()) return '请填写券名称'
  // 补送券无金额/门槛，只校验名称与有效期；满减券才校验金额门槛
  if (!isReissueForm.value) {
    if (!(Number(form.amount) > 0)) return '抵扣金额需大于0'
    if (Number(form.minSpend) < 0) return '使用门槛不能为负'
  }
  if (!(Number(form.validDays) > 0)) return '有效天数需大于0'
  return ''
}

async function save() {
  const message = validate()
  if (message) {
    uni.showToast({ title: message, icon: 'none' })
    return
  }
  saving.value = true
  const isReissue = form.kind === 'reissue'
  const payload = {
    name: form.name.trim(),
    description: form.description.trim() || null,
    kind: form.kind,
    // 补送券无金额/门槛/自动发放，后端也会兜底归零，这里同步传 0/false 保持一致
    amount: isReissue ? 0 : Number(form.amount),
    min_spend: isReissue ? 0 : Number(form.minSpend || 0),
    valid_days: Number(form.validDays),
    grant_on_verified: isReissue ? false : form.grantOnVerified,
    per_customer_limit: 1,
    is_active: form.isActive,
  }
  try {
    if (editingId.value) {
      await request({ url: `/admin/coupon-templates/${editingId.value}`, method: 'PATCH', admin: true, data: payload })
    } else {
      await request({ url: '/admin/coupon-templates', method: 'POST', admin: true, data: payload })
    }
    modalVisible.value = false
    await loadTemplates()
    uni.showToast({ title: '已保存', icon: 'success' })
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
  } finally {
    saving.value = false
  }
}

async function openGrant() {
  if (!activeTemplates.value.length) {
    uni.showToast({ title: '请先创建并启用券种', icon: 'none' })
    return
  }
  if (!customers.value.length) {
    try {
      customers.value = await request({ url: '/admin/customers', admin: true })
    } catch (err) {
      uni.showToast({ title: err.message, icon: 'none' })
      return
    }
  }
  grantVisible.value = true
}

async function handleGrant({ customerId, templateId }) {
  granting.value = true
  try {
    await request({ url: `/admin/customers/${customerId}/coupons`, method: 'POST', admin: true, data: { template_id: templateId } })
    grantVisible.value = false
    uni.showToast({ title: '已发放', icon: 'success' })
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
  } finally {
    granting.value = false
  }
}

function guardedLoad() {
  if (redirectIfNoPermission('coupons')) return
  loadTemplates()
}

onMounted(guardedLoad)
onShow(guardedLoad)

onPullDownRefresh(async () => {
  try {
    await loadTemplates()
  } finally {
    uni.stopPullDownRefresh()
  }
})
</script>

<template>
  <view class="page">
    <view class="admin-nav">
      <button v-for="item in navItems" :key="item.key" class="nav-button" :class="{ active: item.key === 'coupons' }" @tap="goAdminNav(item)">{{ item.label }}</button>
    </view>

    <view class="top-actions">
      <button class="create-btn" @tap="openCreate">+ 新建券种</button>
      <button class="grant-btn" @tap="openGrant">发券给用户</button>
    </view>

    <view v-if="loading && !templates.length" class="empty">正在加载券种...</view>
    <view v-else-if="!templates.length" class="empty">还没有券种，点击上方新建</view>

    <view v-for="template in templates" :key="template.id" class="card" @tap="openEdit(template)">
      <view class="card-head">
        <view class="tpl-name-row">
          <text class="tpl-name">{{ template.name }}</text>
          <text class="tpl-kind" :class="{ reissue: template.kind === 'reissue' }">{{ template.kind === 'reissue' ? '补送券' : '满减券' }}</text>
        </view>
        <text class="tpl-state" :class="{ off: !template.is_active }">{{ template.is_active ? '启用中' : '已停用' }}</text>
      </view>
      <view v-if="template.kind === 'reissue'" class="tpl-amount reissue">随单免费补配</view>
      <view v-else class="tpl-amount">¥{{ money(template.amount) }} <text class="tpl-cond">{{ Number(template.min_spend) > 0 ? `满${money(template.min_spend)}可用` : '无门槛' }}</text></view>
      <view class="tpl-meta">有效期 {{ template.valid_days }} 天 · {{ template.kind === 'reissue' ? '仅手动发放' : (template.grant_on_verified ? '认证通过自动发放' : '不自动发放') }}</view>
      <view v-if="template.description" class="tpl-desc">{{ template.description }}</view>
    </view>

    <view v-if="modalVisible" class="modal-mask" @tap="closeModal">
      <view class="modal-card" @tap.stop>
        <view class="modal-title">{{ editingId ? '编辑券种' : '新建券种' }}</view>
        <view class="field">
          <text class="label">券类型</text>
          <view class="kind-tabs">
            <view class="kind-tab" :class="{ on: form.kind === 'discount' }" @tap="form.kind = 'discount'">满减券</view>
            <view class="kind-tab" :class="{ on: form.kind === 'reissue' }" @tap="form.kind = 'reissue'">补送券</view>
          </view>
          <text class="kind-tip">{{ isReissueForm ? '补送券无金额门槛，随单免费补配对应商品，可与满减券叠加、多张同用，仅手动发放。' : '满减券按门槛抵扣金额，每单限用一张。' }}</text>
        </view>
        <view class="field">
          <text class="label">{{ isReissueForm ? '补送内容（作为券名，如 补送-芒果1个）' : '券名称' }}</text>
          <input v-model="form.name" class="input" :placeholder="isReissueForm ? '如 补送-草莓1盒' : '如 认证专享券'" />
        </view>
        <template v-if="!isReissueForm">
          <view class="field">
            <text class="label">抵扣金额（元）</text>
            <input v-model="form.amount" class="input" type="digit" placeholder="如 10" />
          </view>
          <view class="field">
            <text class="label">使用门槛（满多少元，0 为无门槛）</text>
            <input v-model="form.minSpend" class="input" type="digit" placeholder="如 100" />
          </view>
        </template>
        <view class="field">
          <text class="label">有效天数（领取后）</text>
          <input v-model="form.validDays" class="input" type="number" placeholder="如 30" />
        </view>
        <view v-if="!isReissueForm" class="switch-row">
          <text class="label">认证通过自动发放</text>
          <switch :checked="form.grantOnVerified" color="#2f6b23" @change="form.grantOnVerified = $event.detail.value" />
        </view>
        <view class="switch-row">
          <text class="label">启用</text>
          <switch :checked="form.isActive" color="#2f6b23" @change="form.isActive = $event.detail.value" />
        </view>
        <view class="field">
          <text class="label">备注（可选）</text>
          <input v-model="form.description" class="input" placeholder="内部备注" />
        </view>
        <view class="modal-actions">
          <button class="cancel" @tap="closeModal">取消</button>
          <button class="save" :loading="saving" :disabled="saving" @tap="save">保存</button>
        </view>
      </view>
    </view>

    <coupon-grant-modal
      :visible="grantVisible"
      :templates="activeTemplates"
      :customers="customers"
      :saving="granting"
      @close="grantVisible = false"
      @confirm="handleGrant"
    />
  </view>
</template>

<style scoped>
.page { min-height: 100vh; padding: 24rpx; background: #f5f8ef; box-sizing: border-box; }
.admin-nav { display: flex; gap: 10rpx; margin-bottom: 20rpx; }
.nav-button { flex: 1; height: 70rpx; line-height: 70rpx; padding: 0; border-radius: 999rpx; color: #2f4b21; background: #fff; font-size: 23rpx; }
.nav-button.active { color: #fff; background: #2f6b23; }
.nav-button::after { border: none; }

.top-actions { display: flex; gap: 14rpx; }
.create-btn, .grant-btn {
  flex: 1;
  height: 84rpx;
  line-height: 84rpx;
  border-radius: 18rpx;
  font-size: 28rpx;
  font-weight: 800;
}
.create-btn {
  color: #fff;
  background: #2f6b23;
}
.grant-btn {
  color: #2f6b23;
  background: #eef7e6;
}
.create-btn::after, .grant-btn::after { border: none; }

.card, .empty { margin-top: 18rpx; padding: 24rpx; border-radius: 26rpx; background: #fff; box-shadow: 0 10rpx 26rpx rgba(73,83,47,.08); }
.empty { text-align: center; color: #7a8a72; font-size: 26rpx; }

.card-head { display: flex; align-items: center; justify-content: space-between; }
.tpl-name-row { display: flex; align-items: center; gap: 12rpx; min-width: 0; }
.tpl-name { color: #173b16; font-size: 30rpx; font-weight: 900; }
.tpl-kind { flex: 0 0 auto; padding: 4rpx 14rpx; border-radius: 999rpx; color: #b26a00; background: #fff2df; font-size: 21rpx; font-weight: 800; }
.tpl-kind.reissue { color: #1f7a52; background: #e4f6ec; }
.tpl-state { color: #2f6b23; font-size: 23rpx; font-weight: 800; }
.tpl-state.off { color: #999; }
.tpl-amount { margin-top: 14rpx; color: #f20d2f; font-size: 36rpx; font-weight: 900; }
.tpl-amount.reissue { color: #1f7a52; font-size: 30rpx; }
.tpl-cond { margin-left: 12rpx; color: #ff6a00; font-size: 24rpx; font-weight: 700; }
.tpl-meta { margin-top: 12rpx; color: #60715c; font-size: 24rpx; }
.tpl-desc { margin-top: 8rpx; color: #999; font-size: 23rpx; }

.kind-tabs { display: flex; gap: 12rpx; margin-top: 12rpx; }
.kind-tab { flex: 1; height: 72rpx; line-height: 72rpx; text-align: center; border-radius: 16rpx; color: #60715c; background: #f4f6f0; font-size: 26rpx; font-weight: 800; }
.kind-tab.on { color: #fff; background: #2f6b23; }
.kind-tip { display: block; margin-top: 12rpx; color: #8a9784; font-size: 22rpx; line-height: 1.5; }

.modal-mask {
  position: fixed;
  z-index: 90;
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

.field { margin-top: 22rpx; }
.label { color: #445; font-size: 25rpx; }
.input {
  width: 100%;
  height: 78rpx;
  margin-top: 12rpx;
  padding: 0 22rpx;
  border-radius: 16rpx;
  color: #222;
  background: #f4f6f0;
  box-sizing: border-box;
  font-size: 27rpx;
}

.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 24rpx;
}

.modal-actions { display: flex; gap: 16rpx; margin-top: 34rpx; }
.cancel, .save { flex: 1; height: 82rpx; line-height: 82rpx; border-radius: 16rpx; font-size: 28rpx; font-weight: 800; }
.cancel { color: #555; background: #eef0ea; }
.save { color: #fff; background: #2f6b23; }
.cancel::after, .save::after { border: none; }
</style>
