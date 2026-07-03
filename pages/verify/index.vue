<script setup>
import { computed, reactive, shallowRef } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { request, uploadVerification } from '../../utils/request.js'
import { hasCustomerLogin, loginWithWeChat, isPlaceholderPhone } from '../../utils/auth.js'
import { statusLabel } from '../../utils/format.js'

const loading = shallowRef(false)
const submitting = shallowRef(false)
const imagePath = shallowRef('')
const customer = shallowRef(null)
const verification = shallowRef(null)
const resubmitMode = shallowRef(false)
const hasLoaded = shallowRef(false)

const form = reactive({
  phone: '',
  shopName: '',
  contactName: '',
  businessType: '',
})

const isVerifiedCustomer = computed(() => customer.value?.verification_status === 'verified')
const hasPendingChange = computed(() => isVerifiedCustomer.value && verification.value?.status === 'pending_review')
const hasRejectedChange = computed(() => isVerifiedCustomer.value && verification.value?.status === 'rejected')
const verificationStatus = computed(() => {
  if (isVerifiedCustomer.value && !resubmitMode.value) return 'verified'
  return verification.value?.status || customer.value?.verification_status || 'unverified'
})
const showForm = computed(() => {
  if (isVerifiedCustomer.value) return resubmitMode.value
  return verificationStatus.value === 'unverified' || (verificationStatus.value === 'rejected' && resubmitMode.value)
})
const showStatusCard = computed(() => verificationStatus.value !== 'unverified' && !showForm.value)
const statusTitle = computed(() => {
  if (hasPendingChange.value) return '资料修改待审核'
  if (verificationStatus.value === 'verified') return '店铺已认证'
  if (verificationStatus.value === 'pending_review') return '认证待审核'
  if (verificationStatus.value === 'rejected') return '认证未通过'
  return '提交店铺认证'
})
const statusDesc = computed(() => {
  if (hasPendingChange.value) return '新的认证资料已提交审核，审核期间当前店铺仍保持已认证。'
  if (hasRejectedChange.value) return '认证资料已通过审核，上次修改未通过，可重新提交修改。'
  if (verificationStatus.value === 'verified') return '认证资料已通过审核，订货时会自动使用认证优惠价。'
  if (verificationStatus.value === 'pending_review') return '资料已提交，供应商审核前无需重复提交。'
  if (verificationStatus.value === 'rejected') return '请查看审核备注，修改资料后可以重新提交认证。'
  return '上传门店/档口图片，人工审核后解锁认证优惠价。'
})
const displayInfo = computed(() => {
  const source = isVerifiedCustomer.value ? (customer.value || {}) : (verification.value || customer.value || {})
  // 过滤掉 wx: 开头的占位手机号
  return {
    ...source,
    phone: isPlaceholderPhone(source.phone) ? '' : source.phone,
  }
})
const submitText = computed(() => {
  if (isVerifiedCustomer.value) return '提交修改'
  return verificationStatus.value === 'rejected' ? '重新提交' : '立即认证'
})

function hydrateForm(source = {}, force = false) {
  // 过滤掉 wx: 开头的占位手机号
  const validPhone = [
    source.phone,
    customer.value?.phone,
    uni.getStorageSync('customer_phone'),
  ].find(phone => phone && !isPlaceholderPhone(phone)) || ''
  
  // 只在 force=true 或者用户还没有输入时才填充数据
  if (force || !form.phone) form.phone = validPhone
  if (force || !form.shopName) form.shopName = source.shop_name || customer.value?.shop_name || ''
  if (force || !form.contactName) form.contactName = source.contact_name || customer.value?.contact_name || ''
  if (force || !form.businessType) form.businessType = source.business_type || customer.value?.business_type || ''
}

async function ensureLogin() {
  if (hasCustomerLogin()) return true
  await loginWithWeChat()
  return true
}

async function loadVerification() {
  loading.value = true
  try {
    await ensureLogin()
    customer.value = await request({ url: '/customers/me' })
    uni.setStorageSync('verification_status', customer.value?.verification_status || 'unverified')
    if (customer.value?.phone && !String(customer.value.phone).startsWith('wx:')) {
      uni.setStorageSync('customer_phone', customer.value.phone)
    }
    try {
      verification.value = await request({ url: '/customers/verification/me' })
      // 只在第一次加载时强制填充表单
      hydrateForm(verification.value, !hasLoaded.value)
    } catch (err) {
      verification.value = null
      // 只在第一次加载时强制填充表单
      hydrateForm(customer.value || {}, !hasLoaded.value)
      if (!String(err.message || '').includes('not found') && !String(err.message || '').includes('Not found')) {
        throw err
      }
    }
    hasLoaded.value = true
  } catch (err) {
    uni.showToast({ title: err.message || '认证信息加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function chooseImage() {
  if (!showForm.value) return
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      imagePath.value = res.tempFilePaths[0]
    },
  })
}

function preview(urls, current) {
  if (!urls?.length) return
  uni.previewImage({ urls, current })
}

function startResubmit() {
  resubmitMode.value = true
  imagePath.value = ''
  hydrateForm(isVerifiedCustomer.value ? (customer.value || {}) : (verification.value || {}), true)
}

function cancelResubmit() {
  resubmitMode.value = false
  imagePath.value = ''
  hydrateForm(verification.value || customer.value || {}, true)
}

function validate() {
  if (!form.phone) return '请填写手机号'
  if (!form.shopName) return '请填写店铺名称'
  if (!form.contactName) return '请填写联系人'
  if (!form.businessType) return '请填写经营类型'
  if (!imagePath.value) return '请上传店铺图片'
  return ''
}

async function submitVerification() {
  const message = validate()
  if (message) {
    uni.showToast({ title: message, icon: 'none' })
    return
  }
  submitting.value = true
  try {
    await ensureLogin()
    uni.setStorageSync('customer_phone', form.phone)
    verification.value = await uploadVerification({
      filePath: imagePath.value,
      formData: {
        phone: form.phone,
        shop_name: form.shopName,
        contact_name: form.contactName,
        business_type: form.businessType,
      },
    })
    resubmitMode.value = false
    imagePath.value = ''
    await loadVerification()
    uni.showModal({
      title: isVerifiedCustomer.value ? '已提交修改' : '已提交认证',
      content: isVerifiedCustomer.value ? '修改资料已提交审核，审核通过后会更新认证资料；审核期间不影响认证优惠价。' : '认证状态为待审核，供应商审核通过后即可享受优惠价。',
      showCancel: false,
    })
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
  } finally {
    submitting.value = false
  }
}

onShow(loadVerification)

onPullDownRefresh(async () => {
  try {
    await loadVerification()
  } finally {
    uni.stopPullDownRefresh()
  }
})
</script>

<template>
  <view class="page" :class="{ 'no-bottom': !showForm }">
    <view class="banner">
      <view class="banner-title">认证店铺信息可享超低价</view>
      <view class="banner-sub">{{ statusDesc }}</view>
    </view>

    <view v-if="loading" class="form-card empty">正在加载认证信息...</view>

    <view v-if="!loading && showStatusCard" class="status-card" :class="verificationStatus">
      <view class="status-head">
        <view>
          <view class="status-title">{{ statusTitle }}</view>
          <view class="status-sub">{{ statusDesc }}</view>
        </view>
        <view class="status-badge">{{ statusLabel(verificationStatus) }}</view>
      </view>
      <view class="info-grid">
        <view class="info-row"><text>店铺名称</text><strong>{{ displayInfo.shop_name || '-' }}</strong></view>
        <view class="info-row"><text>联系人</text><strong>{{ displayInfo.contact_name || '-' }}</strong></view>
        <view class="info-row"><text>手机号</text><strong>{{ displayInfo.phone || '-' }}</strong></view>
        <view class="info-row"><text>经营类型</text><strong>{{ displayInfo.business_type || '-' }}</strong></view>
      </view>
      <view v-if="hasPendingChange" class="review-note">新的认证资料正在审核中，审核通过后会更新展示资料。</view>
      <view v-if="hasRejectedChange && verification?.review_note" class="review-note">上次修改未通过：{{ verification.review_note }}</view>
      <view v-if="!isVerifiedCustomer && verification?.review_note" class="review-note">审核备注：{{ verification.review_note }}</view>
      <view v-if="verification?.image_urls?.length" class="history-images">
        <image v-for="url in verification.image_urls" :key="url" class="history-image" :src="url" mode="aspectFill" @tap="preview(verification.image_urls, url)" />
      </view>
      <button v-if="verificationStatus === 'rejected' && !isVerifiedCustomer" class="resubmit" @tap="startResubmit">重新提交认证</button>
      <button v-if="isVerifiedCustomer && !hasPendingChange" class="resubmit" @tap="startResubmit">修改认证资料</button>
      <button v-if="hasPendingChange" class="resubmit disabled" disabled>修改审核中</button>
    </view>

    <template v-if="!loading && showForm">
      <view v-if="isVerifiedCustomer || verificationStatus === 'rejected'" class="status-card small" :class="isVerifiedCustomer ? 'verified' : 'rejected'">
        <view class="status-title">{{ isVerifiedCustomer ? '修改认证资料' : '认证未通过' }}</view>
        <view class="status-sub">{{ isVerifiedCustomer ? '请提交新的店铺资料和图片，审核通过后会更新认证资料。' : (verification?.review_note || '请修改认证资料后重新提交。') }}</view>
        <button class="cancel" @tap="cancelResubmit">取消</button>
      </view>

      <view class="form-card">
        <view class="card-title">店铺资料</view>
        <input v-model="form.phone" class="input" type="number" placeholder="手机号" />
        <input v-model="form.shopName" class="input" placeholder="店铺/档口名称" />
        <input v-model="form.contactName" class="input" placeholder="联系人" />
        <input v-model="form.businessType" class="input" placeholder="经营类型，如水果店/超市/餐饮" />
      </view>

      <view class="form-card">
        <view class="card-title">店铺图片</view>
        <view class="upload" @tap="chooseImage">
          <image v-if="imagePath" class="preview" :src="imagePath" mode="aspectFill" />
          <view v-else class="upload-empty">
            <view class="upload-icon">＋</view>
            <view class="upload-text">上传店铺图片</view>
            <view class="upload-hint">建议包含门头、货架或档口环境</view>
          </view>
        </view>
      </view>
    </template>

    <view v-if="showForm" class="bottom-bar">
      <button class="submit" :loading="submitting" :disabled="submitting" @tap="submitVerification">{{ submitText }}</button>
    </view>
  </view>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding-bottom: 130rpx;
  background: #f3f3f3;
}

.page.no-bottom {
  padding-bottom: 36rpx;
}

.banner {
  margin: 26rpx;
  padding: 30rpx;
  border-radius: 26rpx;
  background: linear-gradient(180deg, #ff5757, #ff7a45 52%, #ffe6dc);
  color: #fff;
}

.banner-title { font-size: 34rpx; font-weight: 900; }
.banner-sub { margin-top: 10rpx; font-size: 25rpx; opacity: .92; }
.form-card,
.status-card {
  margin: 24rpx 26rpx 0;
  padding: 28rpx;
  border-radius: 22rpx;
  background: #fff;
}

.empty { text-align: center; color: #777; font-size: 27rpx; }
.card-title { margin-bottom: 8rpx; color: #222; font-size: 32rpx; font-weight: 900; }
.input { width: 100%; height: 78rpx; margin-top: 16rpx; padding: 0 22rpx; border-radius: 16rpx; color: #222; background: #f6f6f6; box-sizing: border-box; font-size: 27rpx; }

.status-card { border: 2rpx solid transparent; }
.status-card.pending_review { border-color: #ffd06b; background: #fffaf0; }
.status-card.verified { border-color: #c7e8b9; background: #f5fff0; }
.status-card.rejected { border-color: #fecaca; background: #fff7f7; }
.status-card.small { padding-bottom: 22rpx; }
.status-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 18rpx; }
.status-title { color: #173b16; font-size: 36rpx; font-weight: 900; }
.status-sub { margin-top: 10rpx; color: #60715c; font-size: 26rpx; line-height: 1.5; }
.status-badge { flex-shrink: 0; padding: 8rpx 16rpx; border-radius: 999rpx; color: #fff; background: #ffb700; font-size: 24rpx; font-weight: 900; }
.status-card.verified .status-badge { background: #2f6b23; }
.status-card.rejected .status-badge { background: #ef4444; }
.info-grid { margin-top: 24rpx; border-top: 1rpx solid rgba(96, 113, 92, .16); }
.info-row { display: flex; justify-content: space-between; gap: 20rpx; padding: 18rpx 0; border-bottom: 1rpx solid rgba(96, 113, 92, .12); color: #60715c; font-size: 26rpx; }
.info-row strong { flex: 1; text-align: right; color: #173b16; }
.review-note { margin-top: 18rpx; padding: 18rpx; border-radius: 16rpx; color: #9a3412; background: #fff2df; font-size: 25rpx; line-height: 1.5; }
.history-images { display: flex; flex-wrap: wrap; gap: 14rpx; margin-top: 20rpx; }
.history-image { width: 160rpx; height: 160rpx; border-radius: 18rpx; background: #eef5e8; }
.resubmit, .cancel { margin-top: 24rpx; height: 76rpx; line-height: 76rpx; border-radius: 999rpx; color: #fff; background: #ff7a22; font-size: 28rpx; font-weight: 900; }
.resubmit.disabled { color: #8a9784; background: #eef1ea; }
.cancel { width: 180rpx; height: 58rpx; line-height: 58rpx; color: #60715c; background: #f0f2ed; font-size: 24rpx; }
.resubmit::after, .cancel::after { border: none; }

.upload {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 320rpx;
  margin-top: 22rpx;
  overflow: hidden;
  border: 2rpx dashed #ffd06b;
  border-radius: 20rpx;
  background: #fffaf0;
}

.preview { width: 100%; height: 100%; }
.upload-empty { text-align: center; color: #777; }
.upload-icon { color: #ffb700; font-size: 76rpx; }
.upload-text { margin-top: 6rpx; color: #222; font-size: 28rpx; font-weight: 800; }
.upload-hint { margin-top: 8rpx; font-size: 23rpx; }

.bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: var(--window-bottom);
  display: flex;
  align-items: center;
  justify-content: center;
  height: 112rpx;
  padding: 0 26rpx;
  border-top: 1rpx solid #eee;
  background: #fff;
}

.submit { width: 100%; height: 78rpx; line-height: 78rpx; border-radius: 999rpx; color: #fff; background: linear-gradient(90deg, #ff315f, #ff7a22, #ffd34a); font-size: 34rpx; font-weight: 900; letter-spacing: 4rpx; }
.submit::after { border: none; }
</style>
