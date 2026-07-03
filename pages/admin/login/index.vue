<script setup>
import { onMounted, reactive, shallowRef } from 'vue'
import { onPullDownRefresh } from '@dcloudio/uni-app'
import { request } from '../../../utils/request.js'
import { persistAdminSession, refreshAdminSession } from '../../../utils/admin.js'

const loading = shallowRef(false)
const checking = shallowRef(true)
const form = reactive({ username: 'admin', password: '' })

async function checkExistingLogin() {
  checking.value = true
  const ok = await refreshAdminSession()
  checking.value = false
  if (ok) {
    uni.redirectTo({ url: '/pages/admin/orders/index' })
  }
}

async function login() {
  if (!form.username || !form.password) {
    uni.showToast({ title: '请输入账号和密码', icon: 'none' })
    return
  }
  loading.value = true
  try {
    const data = await request({ url: '/admin/login', method: 'POST', data: form })
    persistAdminSession(data)
    uni.redirectTo({ url: '/pages/admin/orders/index' })
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
  } finally {
    loading.value = false
  }
}

onMounted(checkExistingLogin)

onPullDownRefresh(() => {
  uni.stopPullDownRefresh()
})
</script>

<template>
  <view class="page">
    <view v-if="checking" class="card">
      <view class="title">供应商后台</view>
      <view class="desc">正在检查登录状态...</view>
    </view>
    <view v-else class="card">
      <view class="title">供应商后台</view>
      <view class="desc">不同管理员会按权限显示可管理的模块。</view>
      <input v-model="form.username" class="input" placeholder="管理员账号" />
      <input v-model="form.password" class="input" password placeholder="管理员密码" />
      <button class="submit" :loading="loading" @tap="login">登录</button>
    </view>
  </view>
</template>

<style scoped>
.page { min-height: 100vh; padding: 32rpx; background: #f5f8ef; box-sizing: border-box; }
.card { margin-top: 120rpx; padding: 34rpx; border-radius: 32rpx; background: #fff; box-shadow: 0 14rpx 34rpx rgba(73, 83, 47, 0.08); }
.title { font-size: 44rpx; font-weight: 900; color: #173b16; }
.desc { margin-top: 12rpx; color: #60715c; font-size: 27rpx; }
.input { height: 82rpx; margin-top: 20rpx; padding: 0 24rpx; border-radius: 20rpx; background: #f5f8ef; font-size: 28rpx; }
.submit { margin-top: 28rpx; height: 86rpx; line-height: 86rpx; border-radius: 999rpx; color: #fff; background: #2f6b23; font-size: 30rpx; font-weight: 800; }
</style>
