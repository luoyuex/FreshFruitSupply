<script setup>
import { computed, reactive, ref, shallowRef } from 'vue'
import { onLoad, onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { clearSelectedCartItems } from '../../utils/cart.js'
import { fruitIcon, money } from '../../utils/format.js'
import { request } from '../../utils/request.js'
import { hasCustomerLogin, isPlaceholderPhone, loginWithWeChat } from '../../utils/auth.js'

const orderItems = ref([])
const customer = shallowRef(null)
const loading = shallowRef(false)
const submitting = shallowRef(false)
const goodsPickerVisible = shallowRef(false)
const goodsLoading = shallowRef(false)
const checkoutFromCart = shallowRef(false)
const editingOrderId = shallowRef('')
const editAllowed = shallowRef(true)
const pageQuery = shallowRef({})
const defaultAddressLoaded = shallowRef(false)
const fruitOptions = ref([])
const productKeyword = shallowRef('')
const form = reactive({
  customerPhone: uni.getStorageSync('customer_phone') || '',
  receiverName: '',
  receiverPhone: '',
  province: '',
  city: '',
  district: '',
  detailAddress: '',
  deliveryNote: '',
})

const isVerified = computed(() => customer.value?.verification_status === 'verified')
const isEditMode = computed(() => Boolean(editingOrderId.value))
const estimatedTotal = computed(() => orderItems.value.reduce((sum, item) => sum + activePrice(item) * Number(item.quantity || 0), 0))
const filteredFruitOptions = computed(() => {
  const keyword = productKeyword.value.trim().toLowerCase()
  if (!keyword) return fruitOptions.value
  return fruitOptions.value.filter((fruit) => {
    return [fruit.name, fruit.origin, fruit.spec, fruit.category]
      .filter(Boolean)
      .some((text) => String(text).toLowerCase().includes(keyword))
  })
})
const addressSummary = computed(() => {
  const full = `${form.province || ''}${form.city || ''}${form.district || ''}${form.detailAddress || ''}`
  if (!form.receiverName && !form.receiverPhone && !full) return null
  return {
    contact: [form.receiverName, form.receiverPhone].filter(Boolean).join(' '),
    full,
  }
})

function activePrice(item) {
  return Number((isVerified.value ? item.verified_price : item.normal_price) || 0)
}

function displayVerifiedPrice(price) {
  return isVerified.value ? `¥${money(price)}` : '???'
}

// 商品封面：优先多图第一张，回退单图字段，取不到再由模板兜底 emoji
function primaryImage(fruit) {
  return fruit.image_urls?.[0] || fruit.image_url || ''
}

function normalizeFruit(fruit, quantity) {
  const quote = fruit.quote || {}
  const price = isVerified.value ? quote.verified_price : quote.normal_price
  return {
    id: fruit.id,
    name: fruit.name,
    spec: fruit.spec,
    unit: fruit.unit,
    image: primaryImage(fruit),
    quantity: Number(quantity || quote.min_order_quantity || 1),
    normal_price: Number(quote.normal_price || 0),
    verified_price: Number(quote.verified_price || quote.normal_price || 0),
    price: Number(price || 0),
  }
}

function normalizeOrderItem(item) {
  const price = Number(item.price || 0)
  return {
    id: item.fruit_id,
    name: item.fruit_name,
    spec: item.spec,
    unit: item.unit,
    image: item.image_url || '',
    quantity: Number(item.quantity || 1),
    normal_price: price,
    verified_price: price,
    price,
  }
}

function normalizeCartItem(item) {
  const normal = item.normal_price ?? item.quote?.normal_price ?? 0
  const verified = item.verified_price ?? item.quote?.verified_price ?? normal
  const price = isVerified.value ? verified : normal
  return {
    id: item.id,
    name: item.name,
    spec: item.spec,
    unit: item.unit,
    image: item.image_url || item.image_urls?.[0] || '',
    quantity: Number(item.quantity || item.min_order_quantity || item.quote?.min_order_quantity || 1),
    normal_price: Number(normal || 0),
    verified_price: Number(verified || 0),
    price: Number(price || 0),
  }
}

async function loadSingleFruit(id) {
  loading.value = true
  try {
    const fruit = await request({ url: `/fruits/${id}` })
    orderItems.value = [normalizeFruit(fruit)]
  } catch (err) {
    orderItems.value = []
    uni.showToast({ title: err.message || '商品加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function loadCartItems() {
  try {
    const items = JSON.parse(uni.getStorageSync('checkout_items') || '[]')
    orderItems.value = items.map(normalizeCartItem)
  } catch (error) {
    orderItems.value = []
  }
}

async function loadOrderForEdit(id) {
  loading.value = true
  try {
    const order = await request({ url: `/orders/detail/${id}` })
    if (!order.can_edit) {
      editAllowed.value = false
      uni.showToast({ title: '该订单已过修改时间', icon: 'none' })
    } else {
      editAllowed.value = true
    }
    form.customerPhone = order.receiver_phone
    form.receiverName = order.receiver_name
    form.receiverPhone = order.receiver_phone
    form.province = order.province
    form.city = order.city
    form.district = order.district
    form.detailAddress = order.detail_address
    form.deliveryNote = order.delivery_note || ''
    orderItems.value = order.items.map(normalizeOrderItem)
  } catch (err) {
    orderItems.value = []
    uni.showToast({ title: err.message || '订单加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

async function loadCustomer() {
  if (!hasCustomerLogin()) return
  try {
    customer.value = await request({ url: '/customers/me' })
    if (!isPlaceholderPhone(customer.value?.phone)) {
      form.customerPhone = form.customerPhone || customer.value.phone
    }
    uni.setStorageSync('verification_status', customer.value?.verification_status || 'unverified')
    orderItems.value = orderItems.value.map((item) => ({ ...item, price: activePrice(item) }))
  } catch (err) {
    customer.value = null
  }
}

async function ensureCustomerLogin() {
  if (hasCustomerLogin()) return true
  loading.value = true
  try {
    const data = await loginWithWeChat()
    customer.value = data.customer
    if (!isPlaceholderPhone(data.customer?.phone)) {
      form.customerPhone = form.customerPhone || data.customer.phone
    }
    uni.showToast({ title: '登录成功', icon: 'success' })
    return true
  } catch (err) {
    uni.showToast({ title: err.message || '请先登录', icon: 'none' })
    return false
  } finally {
    loading.value = false
  }
}

function hasAddressInput() {
  return Boolean(form.receiverName || form.receiverPhone || form.province || form.city || form.district || form.detailAddress)
}

function parseStoredAddress(raw) {
  if (!raw) return null
  if (typeof raw === 'object') return raw
  try {
    return JSON.parse(raw)
  } catch (error) {
    return null
  }
}

function applyAddress(address, overwrite = false) {
  if (!address || (!overwrite && hasAddressInput())) return
  form.receiverName = address.receiver_name || ''
  form.receiverPhone = address.receiver_phone || ''
  form.customerPhone = form.customerPhone || address.receiver_phone || ''
  form.province = address.province || ''
  form.city = address.city || ''
  form.district = address.district || ''
  form.detailAddress = address.detail_address || ''
  form.deliveryNote = address.delivery_note || ''
}

function consumeSelectedAddress() {
  const address = parseStoredAddress(uni.getStorageSync('selected_address'))
  if (!address) return
  applyAddress(address, true)
  uni.removeStorageSync('selected_address')
}

async function loadDefaultAddress() {
  if (isEditMode.value || defaultAddressLoaded.value || !hasCustomerLogin() || hasAddressInput()) return
  defaultAddressLoaded.value = true
  try {
    const addresses = await request({ url: '/addresses' })
    const address = addresses.find((item) => item.is_default) || addresses[0]
    applyAddress(address)
  } catch (err) {
    // 默认地址只是辅助回填，失败不影响手动填写和提交订单。
  }
}

async function chooseSavedAddress() {
  if (!(await ensureCustomerLogin())) return
  uni.navigateTo({ url: '/pages/address/index?select=1' })
}

async function addSavedAddress() {
  if (!(await ensureCustomerLogin())) return
  uni.navigateTo({ url: '/pages/address/index?select=1&add=1' })
}

function changeQuantity(item, delta) {
  item.quantity = Math.max(1, Number(item.quantity || 1) + delta)
}

function removeItem(item) {
  if (orderItems.value.length <= 1) {
    uni.showToast({ title: '至少保留一个商品', icon: 'none' })
    return
  }
  uni.showModal({
    title: '删除商品',
    content: `确认从订单中删除 ${item.name}？`,
    success: (res) => {
      if (!res.confirm) return
      orderItems.value = orderItems.value.filter((line) => line.id !== item.id)
    },
  })
}

function isInOrder(fruit) {
  return orderItems.value.some((item) => item.id === fruit.id)
}

async function loadFruitOptions() {
  if (fruitOptions.value.length) return
  goodsLoading.value = true
  try {
    fruitOptions.value = await request({ url: '/fruits' })
  } catch (err) {
    uni.showToast({ title: err.message || '商品加载失败', icon: 'none' })
  } finally {
    goodsLoading.value = false
  }
}

async function openGoodsPicker() {
  if (isEditMode.value && !editAllowed.value) {
    uni.showToast({ title: '该订单已过修改时间', icon: 'none' })
    return
  }
  productKeyword.value = ''
  goodsPickerVisible.value = true
  await loadFruitOptions()
}

function closeGoodsPicker() {
  goodsPickerVisible.value = false
}

function addFruitToOrder(fruit) {
  if (fruit.stock_status === 'out_of_stock') {
    uni.showToast({ title: '该商品已售罄', icon: 'none' })
    return
  }
  const existing = orderItems.value.find((item) => item.id === fruit.id)
  const minQuantity = Number(fruit.quote?.min_order_quantity || 1)
  if (existing) {
    existing.quantity = Number(existing.quantity || 0) + minQuantity
    uni.showToast({ title: '数量已增加', icon: 'success' })
    return
  }
  orderItems.value = [...orderItems.value, normalizeFruit(fruit, minQuantity)]
  uni.showToast({ title: '已加入订单', icon: 'success' })
}

function validate() {
  if (!orderItems.value.length) return '没有可提交的商品'
  if (!form.customerPhone) return '请填写下单手机号'
  if (!form.receiverName) return '请填写收货人'
  if (!form.receiverPhone) return '请填写收货手机号'
  if (!form.province || !form.city || !form.district || !form.detailAddress) return '请填写完整配送地址'
  return ''
}

async function submitOrder() {
  const message = validate()
  if (message) {
    uni.showToast({ title: message, icon: 'none' })
    return
  }
  submitting.value = true
  try {
    await request({
      url: isEditMode.value ? `/orders/${editingOrderId.value}` : '/orders',
      method: isEditMode.value ? 'PATCH' : 'POST',
      data: {
        customer_phone: form.customerPhone,
        receiver_name: form.receiverName,
        receiver_phone: form.receiverPhone,
        province: form.province,
        city: form.city,
        district: form.district,
        detail_address: form.detailAddress,
        delivery_note: form.deliveryNote,
        items: orderItems.value.map((item) => ({ fruit_id: item.id, quantity: Number(item.quantity) })),
      },
    })
    if (checkoutFromCart.value) {
      clearSelectedCartItems(orderItems.value.map((item) => item.id))
      uni.removeStorageSync('checkout_items')
    }
    uni.showModal({
      title: isEditMode.value ? '订单已修改' : '预订已提交',
      content: isEditMode.value ? '订单修改已保存，22:30后将不能再修改。' : '供应商会尽快联系你确认库存、价格和配送，无需线上支付。',
      showCancel: false,
      success: () => uni.switchTab({ url: '/pages/mine/index' }),
    })
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
  } finally {
    submitting.value = false
  }
}

async function reloadOrder(query = pageQuery.value) {
  await loadCustomer()
  editingOrderId.value = query.edit || ''
  editAllowed.value = true
  if (editingOrderId.value) {
    await loadOrderForEdit(editingOrderId.value)
    return
  }
  defaultAddressLoaded.value = false
  checkoutFromCart.value = query.cart === '1'
  if (checkoutFromCart.value) {
    loadCartItems()
    await loadDefaultAddress()
    return
  }
  await loadSingleFruit(query.id)
  await loadDefaultAddress()
}

onLoad(async (query) => {
  pageQuery.value = query || {}
  await reloadOrder(pageQuery.value)
})

onShow(() => {
  consumeSelectedAddress()
})

onPullDownRefresh(async () => {
  try {
    await reloadOrder()
  } finally {
    uni.stopPullDownRefresh()
  }
})
</script>

<template>
  <view class="page">

    <view class="tip-strip">{{ isEditMode ? '订单可在每天22:30前修改，之后车辆准备出发。' : '提交后无需线上支付，供应商会电话/微信确认配送。' }}</view>

    <view class="card">
      <view class="card-title-row">
        <view class="card-title">商品清单</view>
        <button class="goods-add" :disabled="isEditMode && !editAllowed" @tap="openGoodsPicker">添加商品</button>
      </view>
      <view v-for="item in orderItems" :key="item.id" class="goods-row">
        <view class="goods-img">
          <image v-if="item.image" class="goods-image" :src="item.image" mode="aspectFill" />
          <text v-else>{{ fruitIcon(item.name) }}</text>
        </view>
        <view class="goods-info">
          <view class="goods-name">{{ item.name }}</view>
          <view class="goods-spec">{{ item.spec }}</view>
          <view class="goods-price">¥{{ money(activePrice(item) * item.quantity) }}</view>
        </view>
        <view class="item-controls">
          <view class="stepper">
            <button class="step" :disabled="isEditMode && !editAllowed" @tap="changeQuantity(item, -1)">−</button>
            <text class="quantity">{{ item.quantity }}</text>
            <button class="step" :disabled="isEditMode && !editAllowed" @tap="changeQuantity(item, 1)">＋</button>
          </view>
          <button class="remove-goods" :disabled="isEditMode && !editAllowed" @tap="removeItem(item)">删除</button>
        </view>
      </view>
      <view class="total">预估合计 <text>¥{{ money(estimatedTotal) }}</text></view>
    </view>

    <view class="card">
      <view class="card-title-row">
        <view class="card-title">配送信息</view>
        <view class="address-tools">
          <button class="address-tool" @tap="chooseSavedAddress">选择地址</button>
          <button class="address-tool primary" @tap="addSavedAddress">新增地址</button>
        </view>
      </view>
      <view v-if="addressSummary" class="selected-address" @tap="chooseSavedAddress">
        <view class="selected-contact">{{ addressSummary.contact || '已选择配送地址' }}</view>
        <view class="selected-full">{{ addressSummary.full }}</view>
      </view>
      <input v-model="form.customerPhone" class="input" type="number" placeholder="下单手机号，用于识别认证价" @blur="loadCustomer" />
      <input v-model="form.receiverName" class="input" placeholder="收货人姓名" />
      <input v-model="form.receiverPhone" class="input" type="number" placeholder="收货手机号" />
      <view class="address-grid">
        <input v-model="form.province" class="input" placeholder="省" />
        <input v-model="form.city" class="input" placeholder="市" />
        <input v-model="form.district" class="input" placeholder="区/县" />
      </view>
      <textarea v-model="form.detailAddress" class="textarea" placeholder="详细地址，例如市场、门店、档口号" />
      <textarea v-model="form.deliveryNote" class="textarea" placeholder="配送备注，例如到货时间、卸货位置，可不填" />
    </view>

    <view v-if="goodsPickerVisible" class="modal-mask" @tap="closeGoodsPicker">
      <view class="goods-modal" @tap.stop>
        <view class="modal-head">
          <view>
            <view class="modal-title">添加商品</view>
            <view class="modal-sub">从当前真实报价中选择，可重复添加增加数量</view>
          </view>
          <text class="modal-close" @tap="closeGoodsPicker">×</text>
        </view>
        <input v-model="productKeyword" class="search-input" placeholder="搜索水果、产地、规格" />
        <scroll-view class="goods-list" scroll-y>
          <view v-if="goodsLoading" class="picker-empty">正在加载商品...</view>
          <view v-else-if="!filteredFruitOptions.length" class="picker-empty">没有找到商品</view>
          <view
            v-for="fruit in filteredFruitOptions"
            :key="fruit.id"
            class="picker-row"
            :class="{ disabled: fruit.stock_status === 'out_of_stock' }"
            @tap="addFruitToOrder(fruit)"
          >
            <view class="picker-img">
              <image v-if="primaryImage(fruit)" class="goods-image" :src="primaryImage(fruit)" mode="aspectFill" />
              <text v-else>{{ fruitIcon(fruit.name) }}</text>
            </view>
            <view class="picker-info">
              <view class="picker-name">
                <text>{{ fruit.name }}</text>
                <text v-if="isInOrder(fruit)" class="picked-tag">已在订单</text>
              </view>
              <view class="picker-spec">{{ fruit.origin || fruit.category }} · {{ fruit.spec }} / {{ fruit.unit }}</view>
              <view class="picker-price">
                普通 ¥{{ money(fruit.quote?.normal_price || 0) }}
                <text>认证 {{ displayVerifiedPrice(fruit.quote?.verified_price || fruit.quote?.normal_price || 0) }}</text>
              </view>
            </view>
            <button class="picker-add" :disabled="fruit.stock_status === 'out_of_stock'">{{ fruit.stock_status === 'out_of_stock' ? '售罄' : '加入' }}</button>
          </view>
        </scroll-view>
      </view>
    </view>

    <view class="bottom-bar">
      <view class="bottom-total">合计 <text>¥{{ money(estimatedTotal) }}</text></view>
      <button class="submit" :loading="submitting" :disabled="submitting || loading || (isEditMode && !editAllowed)" @tap="submitOrder">{{ isEditMode ? (editAllowed ? '保存修改' : '已截止修改') : '提交预订' }}</button>
    </view>
  </view>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding-bottom: 138rpx;
  background: #f3f3f3;
}



.tip-strip {
  padding: 24rpx 36rpx;
  color: #ff5a00;
  background: #fff2df;
  font-size: 27rpx;
}

.card {
  margin: 26rpx;
  padding: 28rpx;
  border-radius: 22rpx;
  background: #fff;
}

.card-title {
  margin-bottom: 18rpx;
  color: #222;
  font-size: 32rpx;
  font-weight: 800;
}

.card-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  margin-bottom: 18rpx;
}

.card-title-row .card-title { margin-bottom: 0; }

.address-tools {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.address-tool {
  width: 132rpx;
  height: 56rpx;
  line-height: 56rpx;
  border-radius: 999rpx;
  color: #2f6b23;
  background: #eef7e6;
  font-size: 23rpx;
  font-weight: 800;
}

.address-tool::after { border: none; }

.goods-add {
  width: 150rpx;
  height: 58rpx;
  line-height: 58rpx;
  border-radius: 999rpx;
  color: #fff;
  background: #ffb700;
  font-size: 24rpx;
  font-weight: 900;
}

.goods-add[disabled] {
  color: #999;
  background: #eee;
}

.goods-add::after,
.remove-goods::after,
.picker-add::after {
  border: none;
}

.address-tool.primary {
  color: #fff;
  background: #ffb700;
}

.selected-address {
  margin-bottom: 16rpx;
  padding: 20rpx 22rpx;
  border: 2rpx solid #ffe2a3;
  border-radius: 18rpx;
  background: #fffaf0;
}

.selected-contact {
  color: #222;
  font-size: 28rpx;
  font-weight: 900;
}

.selected-full {
  margin-top: 8rpx;
  color: #666;
  font-size: 25rpx;
  line-height: 1.45;
}

.goods-row {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 18rpx 0;
  border-bottom: 1rpx solid #f0f0f0;
}

.goods-img {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 136rpx;
  height: 112rpx;
  overflow: hidden;
  border-radius: 18rpx;
  font-size: 72rpx;
  background: #fafafa;
}

.goods-img .goods-image,
.picker-img .goods-image {
  width: 100%;
  height: 100%;
}

.goods-info { flex: 1; min-width: 0; }
.goods-name { color: #222; font-size: 30rpx; font-weight: 800; }
.goods-spec { margin-top: 10rpx; color: #666; font-size: 25rpx; }
.goods-price { margin-top: 12rpx; color: #f20d2f; font-size: 34rpx; font-weight: 900; }

.item-controls {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12rpx;
}

.stepper {
  display: flex;
  align-items: center;
  height: 52rpx;
  overflow: hidden;
  border-radius: 10rpx;
  background: #f1f2f4;
}

.step { width: 52rpx; height: 52rpx; line-height: 48rpx; color: #333; background: transparent; font-size: 34rpx; }
.step[disabled] { color: #aaa; }
.step::after { border: none; }
.quantity { min-width: 50rpx; text-align: center; color: #222; font-size: 28rpx; }

.remove-goods {
  width: 108rpx;
  height: 46rpx;
  line-height: 46rpx;
  border-radius: 999rpx;
  color: #ef4444;
  background: #fff1f1;
  font-size: 22rpx;
}

.remove-goods[disabled] {
  color: #aaa;
  background: #eee;
}

.total {
  margin-top: 24rpx;
  text-align: right;
  color: #333;
  font-size: 28rpx;
}

.total text,
.bottom-total text {
  color: #f20d2f;
  font-size: 40rpx;
  font-weight: 900;
}

.input,
.textarea {
  width: 100%;
  margin-top: 16rpx;
  padding: 0 22rpx;
  border-radius: 16rpx;
  color: #222;
  background: #f6f6f6;
  box-sizing: border-box;
  font-size: 27rpx;
}

.input { height: 78rpx; }
.textarea { height: 134rpx; padding-top: 18rpx; }
.address-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12rpx; }

.modal-mask {
  position: fixed;
  z-index: 90;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  display: flex;
  align-items: flex-end;
  background: rgba(0, 0, 0, .42);
}

.goods-modal {
  width: 100%;
  max-height: 78vh;
  padding: 30rpx 28rpx calc(40rpx + env(safe-area-inset-bottom));
  border-radius: 34rpx 34rpx 0 0;
  background: #fff;
  box-sizing: border-box;
}

.modal-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18rpx;
}

.modal-title {
  color: #173b16;
  font-size: 34rpx;
  font-weight: 900;
}

.modal-sub {
  margin-top: 8rpx;
  color: #777;
  font-size: 24rpx;
}

.modal-close {
  width: 64rpx;
  height: 64rpx;
  line-height: 60rpx;
  text-align: center;
  color: #60715c;
  font-size: 44rpx;
}

.search-input {
  width: 100%;
  height: 78rpx;
  margin-top: 22rpx;
  padding: 0 24rpx;
  border-radius: 999rpx;
  color: #222;
  background: #f5f5f5;
  box-sizing: border-box;
  font-size: 27rpx;
}

.goods-list {
  height: 760rpx;
  max-height: 56vh;
  margin-top: 18rpx;
}

.picker-empty {
  padding: 70rpx 0;
  text-align: center;
  color: #888;
  font-size: 27rpx;
}

.picker-row {
  display: flex;
  align-items: center;
  gap: 18rpx;
  padding: 18rpx 0;
  border-bottom: 1rpx solid #f0f0f0;
}

.picker-row.disabled {
  opacity: .55;
}

.picker-img {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 104rpx;
  height: 92rpx;
  overflow: hidden;
  border-radius: 18rpx;
  background: #fafafa;
  font-size: 56rpx;
}

.picker-info {
  flex: 1;
  min-width: 0;
}

.picker-name {
  display: flex;
  align-items: center;
  gap: 10rpx;
  color: #222;
  font-size: 29rpx;
  font-weight: 900;
}

.picked-tag {
  padding: 4rpx 10rpx;
  border-radius: 999rpx;
  color: #2f6b23;
  background: #eef7e6;
  font-size: 20rpx;
}

.picker-spec {
  margin-top: 8rpx;
  color: #666;
  font-size: 24rpx;
}

.picker-price {
  margin-top: 8rpx;
  color: #f20d2f;
  font-size: 24rpx;
  font-weight: 800;
}

.picker-price text {
  margin-left: 14rpx;
  color: #2f6b23;
}

.picker-add {
  width: 104rpx;
  height: 56rpx;
  line-height: 56rpx;
  border-radius: 999rpx;
  color: #fff;
  background: #ffb700;
  font-size: 23rpx;
  font-weight: 900;
}

.picker-add[disabled] {
  color: #999;
  background: #eee;
}

.bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: var(--window-bottom);
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 112rpx;
  padding: 0 26rpx;
  border-top: 1rpx solid #eee;
  background: #fff;
  box-sizing: border-box;
}

.bottom-total { color: #333; font-size: 28rpx; }
.submit { width: 220rpx; height: 72rpx; line-height: 72rpx; border-radius: 999rpx; color: #fff; background: #ffb700; font-size: 30rpx; font-weight: 800; }
</style>
