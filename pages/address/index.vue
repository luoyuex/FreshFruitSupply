<script setup>
import { onMounted, reactive, shallowRef } from 'vue'
import { onLoad, onPullDownRefresh } from '@dcloudio/uni-app'
import { request } from '../../utils/request.js'

const addresses = shallowRef([])
const loading = shallowRef(false)
const saving = shallowRef(false)
const modalVisible = shallowRef(false)
const selectMode = shallowRef(false)
const editingId = shallowRef(null)
const openAddAfterLoad = shallowRef(false)

const form = reactive({
  receiverName: '',
  receiverPhone: '',
  province: '',
  city: '',
  district: '',
  detailAddress: '',
  deliveryNote: '',
  isDefault: false,
})

function resetForm() {
  editingId.value = null
  Object.assign(form, {
    receiverName: '',
    receiverPhone: '',
    province: '',
    city: '',
    district: '',
    detailAddress: '',
    deliveryNote: '',
    isDefault: addresses.value.length === 0,
  })
}

async function loadAddresses() {
  loading.value = true
  try {
    addresses.value = await request({ url: '/addresses' })
    if (openAddAfterLoad.value && !modalVisible.value) {
      openAddAfterLoad.value = false
      openModal()
    }
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
    if (err.message.includes('login') || err.message.includes('Missing')) {
      setTimeout(() => uni.navigateBack(), 600)
    }
  } finally {
    loading.value = false
  }
}

function openModal(address = null) {
  resetForm()
  if (address) {
    editingId.value = address.id
    Object.assign(form, {
      receiverName: address.receiver_name,
      receiverPhone: address.receiver_phone,
      province: address.province,
      city: address.city,
      district: address.district,
      detailAddress: address.detail_address,
      deliveryNote: address.delivery_note || '',
      isDefault: address.is_default,
    })
  }
  modalVisible.value = true
}

function closeModal() {
  modalVisible.value = false
  resetForm()
}

function validate() {
  if (!form.receiverName) return '请填写收货人'
  if (!form.receiverPhone) return '请填写手机号'
  if (!form.province || !form.city || !form.district) return '请填写省市区'
  if (!form.detailAddress) return '请填写详细地址'
  return ''
}

function toPayload() {
  return {
    receiver_name: form.receiverName,
    receiver_phone: form.receiverPhone,
    province: form.province,
    city: form.city,
    district: form.district,
    detail_address: form.detailAddress,
    delivery_note: form.deliveryNote,
    is_default: form.isDefault,
  }
}

async function saveAddress() {
  const message = validate()
  if (message) {
    uni.showToast({ title: message, icon: 'none' })
    return
  }
  saving.value = true
  try {
    const address = await request({
      url: editingId.value ? `/addresses/${editingId.value}` : '/addresses',
      method: editingId.value ? 'PATCH' : 'POST',
      data: toPayload(),
    })
    uni.showToast({ title: '地址已保存', icon: 'success' })
    closeModal()
    await loadAddresses()
    if (selectMode.value) {
      chooseAddress(address)
    }
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
  } finally {
    saving.value = false
  }
}

function chooseAddress(address) {
  if (!selectMode.value) return
  uni.setStorageSync('selected_address', JSON.stringify(address))
  uni.navigateBack()
}

function editAddress(address) {
  openModal(address)
}

async function setDefault(address) {
  try {
    await request({
      url: `/addresses/${address.id}`,
      method: 'PATCH',
      data: {
        receiver_name: address.receiver_name,
        receiver_phone: address.receiver_phone,
        province: address.province,
        city: address.city,
        district: address.district,
        detail_address: address.detail_address,
        delivery_note: address.delivery_note,
        is_default: true,
      },
    })
    await loadAddresses()
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
  }
}

function deleteAddress(address) {
  uni.showModal({
    title: '删除地址',
    content: `确认删除 ${address.receiver_name} 的地址？`,
    success: async (res) => {
      if (!res.confirm) return
      try {
        await request({ url: `/addresses/${address.id}`, method: 'DELETE' })
        uni.showToast({ title: '已删除', icon: 'success' })
        await loadAddresses()
      } catch (err) {
        uni.showToast({ title: err.message, icon: 'none' })
      }
    },
  })
}

onLoad((query) => {
  selectMode.value = query.select === '1'
  if (query.add === '1') {
    openAddAfterLoad.value = true
  }
})

onMounted(loadAddresses)

onPullDownRefresh(async () => {
  try {
    await loadAddresses()
  } finally {
    uni.stopPullDownRefresh()
  }
})
</script>

<template>
  <view class="page">
    <view class="tip-card">
      <view class="tip-title">{{ selectMode ? '选择配送地址' : '地址管理' }}</view>
      <view class="tip-sub">{{ selectMode ? '点击地址后会自动回填到订单' : '维护常用配送地址，下单时可直接选择' }}</view>
    </view>

    <view v-if="loading" class="empty">正在加载地址...</view>
    <view v-if="!loading && !addresses.length" class="empty">
      <image class="empty-icon" src="/static/icons/map-pin.svg" mode="aspectFit" />
      <view>还没有常用地址</view>
    </view>

    <view v-for="address in addresses" :key="address.id" class="address-card" @tap="chooseAddress(address)">
      <view class="address-head">
        <view>
          <text class="name">{{ address.receiver_name }}</text>
          <text class="phone">{{ address.receiver_phone }}</text>
        </view>
        <text v-if="address.is_default" class="default-tag">默认</text>
      </view>
      <view class="address-text">{{ address.province }}{{ address.city }}{{ address.district }}{{ address.detail_address }}</view>
      <view v-if="address.delivery_note" class="note">备注：{{ address.delivery_note }}</view>
      <view class="actions" @tap.stop>
        <button v-if="!address.is_default" class="action ghost" @tap="setDefault(address)">设为默认</button>
        <button class="action" @tap="editAddress(address)">编辑</button>
        <button class="action danger" @tap="deleteAddress(address)">删除</button>
      </view>
    </view>

    <button class="add-btn" @tap="openModal()">新增地址</button>

    <view v-if="modalVisible" class="modal-mask" @tap="closeModal">
      <view class="modal-card" @tap.stop>
        <view class="modal-head">
          <text class="modal-title">{{ editingId ? '编辑地址' : '新增地址' }}</text>
          <text class="modal-close" @tap="closeModal">×</text>
        </view>
        <input v-model="form.receiverName" class="input" placeholder="收货人" />
        <input v-model="form.receiverPhone" class="input" type="number" placeholder="手机号" />
        <view class="address-grid">
          <input v-model="form.province" class="input" placeholder="省" />
          <input v-model="form.city" class="input" placeholder="市" />
          <input v-model="form.district" class="input" placeholder="区/县" />
        </view>
        <textarea v-model="form.detailAddress" class="textarea" placeholder="详细地址，例如市场、门店、档口号" />
        <textarea v-model="form.deliveryNote" class="textarea" placeholder="配送备注，可不填" />
        <view class="switch-row">
          <text>设为默认地址</text>
          <switch :checked="form.isDefault" @change="form.isDefault = $event.detail.value" />
        </view>
        <button class="save-btn" :loading="saving" @tap="saveAddress">保存地址</button>
      </view>
    </view>
  </view>
</template>

<style scoped>
.page { min-height: 100vh; padding: 24rpx 24rpx 150rpx; background: #f3f3f3; box-sizing: border-box; }
.tip-card, .address-card, .empty { margin-bottom: 22rpx; padding: 28rpx; border-radius: 24rpx; background: #fff; }
.tip-title { color: #173b16; font-size: 36rpx; font-weight: 900; }
.tip-sub { margin-top: 10rpx; color: #777; font-size: 25rpx; }
.empty { text-align: center; color: #888; font-size: 27rpx; }
.empty-icon { width: 72rpx; height: 72rpx; margin-bottom: 12rpx; }
.address-head { display: flex; align-items: center; justify-content: space-between; gap: 18rpx; }
.name { color: #222; font-size: 32rpx; font-weight: 900; }
.phone { margin-left: 18rpx; color: #666; font-size: 27rpx; }
.default-tag { padding: 6rpx 14rpx; border-radius: 999rpx; color: #ff8a00; background: #fff3d2; font-size: 23rpx; }
.address-text { margin-top: 16rpx; color: #333; font-size: 28rpx; line-height: 1.5; }
.note { margin-top: 12rpx; color: #888; font-size: 24rpx; }
.actions { display: flex; justify-content: flex-end; gap: 12rpx; margin-top: 20rpx; }
.action { width: 118rpx; height: 54rpx; line-height: 54rpx; border-radius: 999rpx; color: #fff; background: #ffb700; font-size: 23rpx; }
.action::after, .add-btn::after, .save-btn::after { border: none; }
.action.ghost { color: #2f6b23; background: #eef7e6; }
.action.danger { background: #ef4444; }
.add-btn { position: fixed; left: 26rpx; right: 26rpx; bottom: calc(var(--window-bottom) + 24rpx); height: 84rpx; line-height: 84rpx; border-radius: 999rpx; color: #fff; background: #ffb700; font-size: 30rpx; font-weight: 900; }
.modal-mask { position: fixed; z-index: 99; left: 0; right: 0; top: 0; bottom: 0; display: flex; align-items: flex-end; background: rgba(0, 0, 0, .42); }
.modal-card { width: 100%; padding: 30rpx 28rpx calc(60rpx + env(safe-area-inset-bottom)); border-radius: 34rpx 34rpx 0 0; background: #fff; box-sizing: border-box; }
.modal-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16rpx; }
.modal-title { color: #173b16; font-size: 34rpx; font-weight: 900; }
.modal-close { width: 64rpx; height: 64rpx; line-height: 60rpx; text-align: center; color: #60715c; font-size: 44rpx; }
.input, .textarea { width: 100%; margin-top: 14rpx; padding: 0 22rpx; border-radius: 16rpx; color: #222; background: #f6f6f6; box-sizing: border-box; font-size: 27rpx; }
.input { height: 78rpx; }
.textarea { height: 122rpx; padding-top: 18rpx; }
.address-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12rpx; }
.switch-row { display: flex; align-items: center; justify-content: space-between; margin-top: 18rpx; color: #48613b; font-size: 27rpx; }
.save-btn { margin-top: 22rpx; height: 80rpx; line-height: 80rpx; border-radius: 999rpx; color: #fff; background: #2f6b23; font-size: 29rpx; font-weight: 900; }
</style>
