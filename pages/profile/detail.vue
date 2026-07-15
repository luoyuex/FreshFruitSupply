<script setup>
import { computed, onMounted, reactive, shallowRef } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { statusLabel } from '../../utils/format.js'
import { request, uploadAvatar } from '../../utils/request.js'
import { hasCustomerLogin, isPlaceholderPhone } from '../../utils/auth.js'

const phone = shallowRef(uni.getStorageSync('customer_phone') || '')
const customer = shallowRef(null)
const loading = shallowRef(false)
const saving = shallowRef(false)
const uploading = shallowRef(false)
const form = reactive({
  nickname: '',
  contactName: '',
  phone: '',
})

const isPhoneBound = computed(() => !isPlaceholderPhone(customer.value?.phone) && Boolean(phone.value))
const displayName = computed(() => customer.value?.nickname || customer.value?.shop_name || (phone.value ? `鲜小店${phone.value.slice(-4)}` : '微信用户'))

function syncForm() {
  form.nickname = customer.value?.nickname || ''
  form.contactName = customer.value?.contact_name || ''
  form.phone = !isPlaceholderPhone(customer.value?.phone) ? customer.value.phone : ''
}

async function loadProfile() {
  phone.value = uni.getStorageSync('customer_phone') || ''
  if (!hasCustomerLogin()) {
    customer.value = null
    return
  }
  loading.value = true
  try {
    customer.value = await request({ url: '/customers/me' })
    if (!isPlaceholderPhone(customer.value?.phone)) {
      phone.value = customer.value.phone
      uni.setStorageSync('customer_phone', customer.value.phone)
    } else {
      phone.value = ''
      uni.removeStorageSync('customer_phone')
    }
    uni.setStorageSync('verification_status', customer.value?.verification_status || 'unverified')
    syncForm()
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
  } finally {
    loading.value = false
  }
}

async function saveProfile() {
  if (!hasCustomerLogin()) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    return
  }
  saving.value = true
  try {
    customer.value = await request({
      url: '/customers/me',
      method: 'PATCH',
      data: {
        nickname: form.nickname,
        contact_name: form.contactName,
        phone: form.phone,
      },
    })
    if (!isPlaceholderPhone(customer.value?.phone)) {
      phone.value = customer.value.phone
      uni.setStorageSync('customer_phone', customer.value.phone)
    }
    syncForm()
    uni.showToast({ title: '已保存', icon: 'success' })
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
  } finally {
    saving.value = false
  }
}

function chooseAvatar() {
  if (uploading.value) return
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: async (res) => {
      const tempFilePath = res.tempFilePaths[0]
      await uploadAvatarFunc(tempFilePath)
    },
    fail: (err) => {
      console.error('[chooseAvatar] chooseImage fail:', JSON.stringify(err), err)
      const msg = err?.errMsg || ''
      if (msg.includes('cancel')) return
      uni.showToast({ title: msg || '选择图片失败', icon: 'none' })
    },
  })
}

async function uploadAvatarFunc(filePath) {
  if (!hasCustomerLogin()) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    return
  }
  uploading.value = true
  try {
    const result = await uploadAvatar(filePath)
    customer.value = result
    syncForm()
    uni.showToast({ title: '头像已更新', icon: 'success' })
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
  } finally {
    uploading.value = false
  }
}

function goVerify() {
  uni.navigateTo({ url: '/pages/verify/index' })
}

onMounted(loadProfile)
onShow(loadProfile)

onPullDownRefresh(async () => {
  try {
    await loadProfile()
  } finally {
    uni.stopPullDownRefresh()
  }
})
</script>

<template>
  <view class="page">

    <view class="profile-card">
      <view class="avatar-wrapper" @tap="chooseAvatar">
        <image v-if="customer?.avatar_url" class="avatar" :src="customer.avatar_url" mode="aspectFill" />
        <view v-else class="avatar">🍊</view>
        <view v-if="!uploading" class="edit-icon">✏️</view>
      </view>
      <view class="profile-main">
        <view class="profile-name">{{ displayName }}</view>
        <view class="profile-sub">{{ isPhoneBound ? `手机号：${phone}` : '已微信登录，手机号可自行填写' }}</view>
      </view>
    </view>

    <view class="info-card">
      <view class="section-title">用户信息</view>
      <view class="edit-row">
        <text class="info-label">昵称</text>
        <input v-model="form.nickname" class="edit-input" placeholder="填写昵称" />
      </view>
      <view class="edit-row">
        <text class="info-label">联系人</text>
        <input v-model="form.contactName" class="edit-input" placeholder="填写联系人，选填" />
      </view>
      <view class="edit-row">
        <text class="info-label">手机号</text>
        <input v-model="form.phone" class="edit-input" type="number" placeholder="自行填写手机号，选填" />
      </view>
      <button class="save-btn" :loading="saving" @tap="saveProfile">保存用户信息</button>
    </view>

    <view class="info-card">
      <view class="section-title">认证信息</view>
      <view class="info-row">
        <text class="info-label">认证状态</text>
        <text class="info-value highlight">{{ statusLabel(customer?.verification_status || 'unverified') }}</text>
      </view>
      <view class="info-row">
        <text class="info-label">店铺名称</text>
        <text class="info-value">{{ customer?.shop_name || '未认证' }}</text>
      </view>
      <view class="info-row">
        <text class="info-label">经营类型</text>
        <text class="info-value">{{ customer?.business_type || '-' }}</text>
      </view>
      <button class="verify-btn" :loading="loading" @tap="goVerify">提交/更新认证资料</button>
    </view>
  </view>
</template>

<style scoped>
.page {
  min-height: 100vh;
  background: #f3f3f3;
  padding-bottom: 40rpx;
}





.profile-card,
.info-card {
  margin: 24rpx 26rpx 0;
  border-radius: 22rpx;
  background: #fff;
}

.profile-card {
  display: flex;
  align-items: center;
  gap: 24rpx;
  padding: 32rpx 28rpx;
}

.avatar-wrapper {
  position: relative;
}

.avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 104rpx;
  height: 104rpx;
  border-radius: 50%;
  background: #fff7e5;
  font-size: 66rpx;
  overflow: hidden;
}

.edit-icon {
  position: absolute;
  right: -4rpx;
  bottom: -4rpx;
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  background: #ffb700;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20rpx;
  color: #fff;
  line-height: 1;
}

.profile-main {
  flex: 1;
  min-width: 0;
}

.profile-name {
  color: #333;
  font-size: 36rpx;
  font-weight: 900;
}

.profile-sub {
  margin-top: 12rpx;
  color: #777;
  font-size: 26rpx;
}

.info-card {
  padding: 28rpx;
}

.section-title {
  margin-bottom: 18rpx;
  color: #333;
  font-size: 32rpx;
  font-weight: 900;
}

.info-row,
.edit-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
  min-height: 78rpx;
  border-bottom: 1rpx solid #f1f1f1;
  font-size: 28rpx;
}

.info-row:last-child,
.edit-row:last-child {
  border-bottom: 0;
}

.info-label {
  flex-shrink: 0;
  color: #888;
}

.info-value {
  color: #333;
  text-align: right;
}

.info-value.highlight {
  color: #ff9f00;
  font-weight: 800;
}

.edit-input {
  flex: 1;
  height: 78rpx;
  text-align: right;
  color: #333;
  font-size: 28rpx;
}

.save-btn,
.verify-btn {
  margin-top: 24rpx;
  height: 80rpx;
  line-height: 80rpx;
  border-radius: 999rpx;
  color: #fff;
  font-size: 28rpx;
  font-weight: 800;
}

.save-btn,
.verify-btn {
  background: #ffb700;
}
</style>
