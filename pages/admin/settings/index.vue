<script setup>
import { computed, reactive, shallowRef } from 'vue'
import { onMounted, onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { request } from '../../../utils/request.js'
import { money } from '../../../utils/format.js'
import { goAdminNav, redirectIfNoPermission, visibleAdminNavItems } from '../../../utils/admin.js'

const loading = shallowRef(false)
const saving = shallowRef(false)
const navItems = computed(() => visibleAdminNavItems())

// 配送费配置：低于包邮门槛则收取配送费，门槛与费用均可在此配置
const form = reactive({
  freeThreshold: '',
  fee: '',
})

async function loadConfig() {
  loading.value = true
  try {
    const config = await request({ url: '/admin/settings/delivery', admin: true })
    form.freeThreshold = String(config.free_threshold)
    form.fee = String(config.fee)
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
  } finally {
    loading.value = false
  }
}

function validate() {
  if (form.freeThreshold === '' || Number(form.freeThreshold) < 0) return '请填写有效的包邮门槛'
  if (form.fee === '' || Number(form.fee) < 0) return '请填写有效的配送费'
  return ''
}

async function save() {
  const message = validate()
  if (message) {
    uni.showToast({ title: message, icon: 'none' })
    return
  }
  saving.value = true
  try {
    await request({
      url: '/admin/settings/delivery',
      method: 'PATCH',
      admin: true,
      data: {
        free_threshold: Number(form.freeThreshold),
        fee: Number(form.fee),
      },
    })
    uni.showToast({ title: '已保存', icon: 'success' })
    await loadConfig()
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
  } finally {
    saving.value = false
  }
}

function guardedLoad() {
  if (redirectIfNoPermission('settings')) return
  loadConfig()
}

onMounted(guardedLoad)
onShow(guardedLoad)

onPullDownRefresh(async () => {
  try {
    await loadConfig()
  } finally {
    uni.stopPullDownRefresh()
  }
})
</script>

<template>
  <view class="page">
    <view class="admin-nav">
      <button v-for="item in navItems" :key="item.key" class="nav-button" :class="{ active: item.key === 'settings' }" @tap="goAdminNav(item)">{{ item.label }}</button>
    </view>

    <view class="card">
      <view class="card-title">配送费设置</view>
      <view class="card-desc">订单商品原价合计达到包邮门槛时免配送费，否则按下方金额收取。改动即时对新提交/修改的订单生效。</view>

      <view class="field">
        <text class="label">包邮门槛（元）</text>
        <input v-model="form.freeThreshold" class="input" type="digit" placeholder="如 120" />
      </view>
      <view class="field">
        <text class="label">配送费（元）</text>
        <input v-model="form.fee" class="input" type="digit" placeholder="如 10" />
      </view>

      <view v-if="Number(form.freeThreshold) >= 0 && Number(form.fee) >= 0" class="preview">
        当前规则：满 ¥{{ money(form.freeThreshold || 0) }} 包邮，否则收配送费 ¥{{ money(form.fee || 0) }}
      </view>

      <button class="save" :loading="saving" :disabled="saving || loading" @tap="save">保存</button>
    </view>
  </view>
</template>

<style scoped>
.page { min-height: 100vh; padding: 24rpx; background: #f5f8ef; box-sizing: border-box; }
.admin-nav { display: flex; flex-wrap: wrap; gap: 10rpx; margin-bottom: 20rpx; }
.nav-button { flex: 1; min-width: 120rpx; height: 70rpx; line-height: 70rpx; padding: 0; border-radius: 999rpx; color: #2f4b21; background: #fff; font-size: 23rpx; }
.nav-button.active { color: #fff; background: #2f6b23; }
.nav-button::after { border: none; }

.card { padding: 30rpx 26rpx; border-radius: 26rpx; background: #fff; box-shadow: 0 10rpx 26rpx rgba(73,83,47,.08); }
.card-title { color: #173b16; font-size: 32rpx; font-weight: 900; }
.card-desc { margin-top: 12rpx; color: #7a8a72; font-size: 24rpx; line-height: 1.5; }

.field { margin-top: 26rpx; }
.label { color: #445; font-size: 25rpx; }
.input {
  width: 100%;
  height: 82rpx;
  margin-top: 12rpx;
  padding: 0 22rpx;
  border-radius: 16rpx;
  color: #222;
  background: #f4f6f0;
  box-sizing: border-box;
  font-size: 28rpx;
}

.preview {
  margin-top: 26rpx;
  padding: 20rpx 22rpx;
  border-radius: 16rpx;
  color: #2f6b23;
  background: #eef7e6;
  font-size: 25rpx;
  line-height: 1.5;
}

.save {
  height: 88rpx;
  line-height: 88rpx;
  margin-top: 34rpx;
  border-radius: 18rpx;
  color: #fff;
  background: #2f6b23;
  font-size: 30rpx;
  font-weight: 800;
}
.save::after { border: none; }
</style>
