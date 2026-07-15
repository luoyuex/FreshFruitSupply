<script setup>
import { computed, onMounted, shallowRef } from 'vue'
import { onPullDownRefresh } from '@dcloudio/uni-app'
import { money, statusLabel } from '../../../utils/format.js'
import { request } from '../../../utils/request.js'
import { goAdminNav, visibleAdminNavItems } from '../../../utils/admin.js'

const orders = shallowRef([])
const deliveryOrders = shallowRef([])
const loading = shallowRef(false)
const activeView = shallowRef('orders')
const statuses = ['pending', 'confirmed', 'delivering', 'completed', 'cancelled']
const statusFilterOptions = [{ key: '', label: '全部状态' }, ...statuses.map((status) => ({ key: status, label: statusLabel(status) }))]
const selectedDate = shallowRef(todayDate())
const dateEnabled = shallowRef(true)
const activeStatus = shallowRef('')
const keyword = shallowRef('')
const selectedIds = shallowRef(new Set())
const filteredOrders = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  const statusOrders = activeStatus.value ? orders.value.filter((order) => order.status === activeStatus.value) : orders.value
  if (!text) return statusOrders
  return statusOrders.filter((order) => {
    const address = `${order.province || ''}${order.city || ''}${order.district || ''}${order.detail_address || ''}`
    return [order.order_no, order.receiver_name, order.receiver_phone, address]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(text))
  })
})
const selectableOrders = computed(() => filteredOrders.value.filter((order) => order.status !== 'cancelled' && order.status !== 'completed'))
const selectedCount = computed(() => selectableOrders.value.filter((order) => selectedIds.value.has(order.id)).length)
const allSelected = computed(() => selectableOrders.value.length > 0 && selectableOrders.value.every((order) => selectedIds.value.has(order.id)))
const dateLabel = computed(() => dateEnabled.value ? selectedDate.value : '全部日期')
const activeStatusLabel = computed(() => statusFilterOptions.find((item) => item.key === activeStatus.value)?.label || '全部状态')
const navItems = computed(() => visibleAdminNavItems())

function todayDate() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function buildQuery(params) {
  const query = Object.entries(params)
    .filter(([, value]) => value !== '' && value !== null && value !== undefined)
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    .join('&')
  return query ? `?${query}` : ''
}

async function loadOrders() {
  loading.value = true
  try {
    const query = buildQuery({
      date: dateEnabled.value ? selectedDate.value : '',
      status: activeStatus.value,
    })
    orders.value = await request({ url: `/admin/orders${query}`, admin: true })
    selectedIds.value = new Set([...selectedIds.value].filter((id) => orders.value.some((order) => order.id === id)))
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
    if (err.message.includes('token') || err.message.includes('Missing')) {
      uni.redirectTo({ url: '/pages/admin/login/index' })
    }
  } finally {
    loading.value = false
  }
}

async function changeStatus(order, event) {
  const status = statuses[event.detail.value]
  try {
    await request({ url: `/admin/orders/${order.id}`, method: 'PATCH', admin: true, data: { status } })
    orders.value = orders.value.map((item) => item.id === order.id ? { ...item, status } : item)
    if (status === 'completed' || status === 'cancelled' || (activeStatus.value && activeStatus.value !== status)) {
      const next = new Set(selectedIds.value)
      next.delete(order.id)
      selectedIds.value = next
    }
    uni.showToast({ title: '已更新', icon: 'success' })
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
  }
}

function canSelect(order) {
  return order.status !== 'cancelled' && order.status !== 'completed'
}

function toggleOrder(order) {
  if (!canSelect(order)) return
  const next = new Set(selectedIds.value)
  if (next.has(order.id)) {
    next.delete(order.id)
  } else {
    next.add(order.id)
  }
  selectedIds.value = next
}

function toggleSelectAll() {
  if (allSelected.value) {
    const next = new Set(selectedIds.value)
    selectableOrders.value.forEach((order) => next.delete(order.id))
    selectedIds.value = next
    return
  }
  selectedIds.value = new Set([...selectedIds.value, ...selectableOrders.value.map((order) => order.id)])
}

function clearSelection() {
  selectedIds.value = new Set()
}

async function bulkChangeStatus(status) {
  const orderIds = selectableOrders.value.filter((order) => selectedIds.value.has(order.id)).map((order) => order.id)
  if (!orderIds.length) {
    uni.showToast({ title: '请先选择订单', icon: 'none' })
    return
  }
  uni.showModal({
    title: '批量修改状态',
    content: `确认将 ${orderIds.length} 个订单改为“${statusLabel(status)}”？`,
    success: async (res) => {
      if (!res.confirm) return
      loading.value = true
      try {
        const updatedOrders = await request({
          url: '/admin/orders/bulk-status',
          method: 'PATCH',
          admin: true,
          data: { order_ids: orderIds, status },
        })
        const statusMap = new Map(updatedOrders.map((order) => [order.id, order.status]))
        orders.value = orders.value.map((order) => statusMap.has(order.id) ? { ...order, status: statusMap.get(order.id) } : order)
        clearSelection()
        uni.showToast({ title: '批量更新成功', icon: 'success' })
      } catch (err) {
        uni.showToast({ title: err.message, icon: 'none' })
      } finally {
        loading.value = false
      }
    },
  })
}

function bulkChangeByPicker(event) {
  bulkChangeStatus(statuses[event.detail.value])
}

async function loadDeliverySheet() {
  loading.value = true
  try {
    const query = buildQuery({ date: dateEnabled.value ? selectedDate.value : '' })
    deliveryOrders.value = await request({ url: `/admin/delivery-sheet${query}`, admin: true })
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
  } finally {
    loading.value = false
  }
}

async function changeDate(event) {
  selectedDate.value = event.detail.value
  dateEnabled.value = true
  clearSelection()
  await refreshActiveView()
}

async function setToday() {
  selectedDate.value = todayDate()
  dateEnabled.value = true
  clearSelection()
  await refreshActiveView()
}

async function clearDateFilter() {
  dateEnabled.value = false
  clearSelection()
  await refreshActiveView()
}

async function changeStatusFilter(event) {
  activeStatus.value = statusFilterOptions[event.detail.value]?.key || ''
  clearSelection()
  await loadOrders()
}

async function refreshActiveView() {
  if (activeView.value === 'delivery') {
    await loadDeliverySheet()
  } else {
    await loadOrders()
  }
}

async function switchView(view) {
  activeView.value = view
  if (view === 'delivery') {
    await loadDeliverySheet()
  } else {
    await loadOrders()
  }
}

function printDeliverySheet() {
  uni.showToast({ title: '可截图或复制送货单使用', icon: 'none' })
}

onMounted(async () => {
  await loadOrders()
})

onPullDownRefresh(async () => {
  try {
    if (activeView.value === 'delivery') {
      await loadDeliverySheet()
    } else {
      await loadOrders()
    }
  } finally {
    uni.stopPullDownRefresh()
  }
})
</script>

<template>
  <view class="page">
    <view class="admin-nav">
      <button v-for="item in navItems" :key="item.key" class="nav-button" :class="{ active: item.key === 'orders' }" @tap="goAdminNav(item)">{{ item.label }}</button>
    </view>
    <view class="view-tabs">
      <button class="view-tab" :class="{ active: activeView === 'orders' }" @tap="switchView('orders')">订单列表</button>
      <button class="view-tab" :class="{ active: activeView === 'delivery' }" @tap="switchView('delivery')">送货单</button>
    </view>

    <view class="filter-card">
      <view class="filter-row">
        <picker mode="date" :value="selectedDate" @change="changeDate">
          <view class="filter-pill">日期：{{ dateLabel }}</view>
        </picker>
        <button class="filter-mini" @tap="setToday">今天</button>
        <button class="filter-mini ghost" @tap="clearDateFilter">全部日期</button>
      </view>
      <view v-if="activeView === 'orders'" class="filter-row second">
        <picker :range="statusFilterOptions.map((item) => item.label)" @change="changeStatusFilter">
          <view class="filter-pill">状态：{{ activeStatusLabel }}</view>
        </picker>
        <input v-model="keyword" class="filter-search" placeholder="搜订单号/姓名/手机号/地址" />
      </view>
    </view>

    <view v-if="loading" class="empty">正在加载...</view>

    <template v-if="activeView === 'orders'">
    <view class="bulk-bar">
      <view class="bulk-left">
        <button class="select-all" @tap="toggleSelectAll">{{ allSelected ? '取消全选' : '全选当前' }}</button>
        <text class="selected-count">已选 {{ selectedCount }} 单</text>
      </view>
      <view class="bulk-actions">
        <button class="bulk-btn confirm" @tap="bulkChangeStatus('confirmed')">批量确认</button>
        <button class="bulk-btn delivering" @tap="bulkChangeStatus('delivering')">批量配送中</button>
        <picker :range="statuses.map(statusLabel)" @change="bulkChangeByPicker">
          <view class="bulk-more">更多状态</view>
        </picker>
      </view>
    </view>
    <view v-if="!loading && !filteredOrders.length" class="empty">当前筛选下暂无订单</view>
    <view v-for="order in filteredOrders" :key="order.id" class="card">
      <view class="head">
        <view class="select-line" @tap="toggleOrder(order)">
          <view class="check-dot" :class="{ checked: selectedIds.has(order.id), disabled: !canSelect(order) }">{{ selectedIds.has(order.id) ? '✓' : '' }}</view>
          <text class="order-no">{{ order.order_no }}</text>
        </view>
        <text class="status">{{ statusLabel(order.status) }}</text>
      </view>
      <view class="info">{{ order.receiver_name }} {{ order.receiver_phone }}</view>
      <view class="info">{{ order.province }}{{ order.city }}{{ order.district }}{{ order.detail_address }}</view>
      <view class="info">邮件通知：{{ statusLabel(order.email_notify_status) }}</view>
      <view v-for="item in order.items" :key="item.id" class="item">
        <text>{{ item.fruit_name }} x {{ item.quantity }}{{ item.unit }}</text>
        <text>¥{{ money(item.subtotal) }}</text>
      </view>
      <view v-if="order.reissue_coupons && order.reissue_coupons.length" class="reissue-box">
        <text class="reissue-title">补送商品（随单免费补配）</text>
        <view v-for="coupon in order.reissue_coupons" :key="coupon.id" class="reissue-line">
          <text>· {{ coupon.name }}<text v-if="coupon.description"> （{{ coupon.description }}）</text></text>
        </view>
      </view>
      <view class="total">预估总价 ¥{{ money(order.estimated_total) }}</view>
      <picker :range="statuses.map(statusLabel)" @change="changeStatus(order, $event)">
        <view class="picker">修改状态</view>
      </picker>
    </view>
    </template>

    <template v-else>
      <view class="sheet-head">
        <view>
          <view class="sheet-title">送货单</view>
          <view class="sheet-sub">{{ dateLabel }} · 待确认 / 已确认 / 配送中订单</view>
        </view>
        <button class="print-btn" @tap="printDeliverySheet">使用提示</button>
      </view>
      <view v-if="!deliveryOrders.length && !loading" class="empty">暂无需要配送的订单</view>
      <view v-for="order in deliveryOrders" :key="order.id" class="delivery-card">
        <view class="delivery-head">
          <text>{{ order.receiver_name }} {{ order.receiver_phone }}</text>
          <text class="status">{{ statusLabel(order.status) }}</text>
        </view>
        <view class="info">{{ order.province }}{{ order.city }}{{ order.district }}{{ order.detail_address }}</view>
        <view v-if="order.delivery_note" class="note">备注：{{ order.delivery_note }}</view>
        <view v-for="item in order.items" :key="item.id" class="item">
          <text>{{ item.fruit_name }} · {{ item.spec }}</text>
          <text>{{ item.quantity }}{{ item.unit }}</text>
        </view>
        <view v-if="order.reissue_coupons && order.reissue_coupons.length" class="reissue-box">
          <text class="reissue-title">补送商品（随单免费补配）</text>
          <view v-for="coupon in order.reissue_coupons" :key="coupon.id" class="reissue-line">
            <text>· {{ coupon.name }}<text v-if="coupon.description"> （{{ coupon.description }}）</text></text>
          </view>
        </view>
        <view class="delivery-total">{{ order.order_no }} · ¥{{ money(order.estimated_total) }}</view>
      </view>
    </template>
  </view>
</template>

<style scoped>
.page { min-height: 100vh; padding: 24rpx; background: #f5f8ef; box-sizing: border-box; }
.admin-nav { display: flex; gap: 10rpx; margin-bottom: 20rpx; }
.nav-button { flex: 1; height: 70rpx; line-height: 70rpx; border-radius: 999rpx; color: #2f4b21; background: #fff; font-size: 24rpx; }
.nav-button.active { color: #fff; background: #2f6b23; }
.card, .empty, .delivery-card, .sheet-head { margin-top: 18rpx; padding: 24rpx; border-radius: 26rpx; background: #fff; box-shadow: 0 10rpx 26rpx rgba(73,83,47,.08); }
.view-tabs { display: flex; gap: 14rpx; margin-bottom: 8rpx; }
.view-tab { flex: 1; height: 66rpx; line-height: 66rpx; border-radius: 999rpx; color: #60715c; background: #fff; font-size: 25rpx; }
.view-tab.active { color: #fff; background: #ef7d00; }
.filter-card { margin-top: 18rpx; padding: 18rpx; border-radius: 24rpx; background: #fff; box-shadow: 0 10rpx 26rpx rgba(73,83,47,.08); }
.filter-row { display: flex; align-items: center; gap: 12rpx; }
.filter-row.second { margin-top: 14rpx; }
.filter-pill { height: 60rpx; line-height: 60rpx; padding: 0 22rpx; border-radius: 999rpx; color: #173b16; background: #eef7e6; font-size: 24rpx; font-weight: 800; }
.filter-mini { width: 132rpx; height: 60rpx; line-height: 60rpx; border-radius: 999rpx; color: #fff; background: #2f6b23; font-size: 24rpx; font-weight: 800; }
.filter-mini.ghost { width: 164rpx; color: #60715c; background: #f0f2ed; }
.filter-search { flex: 1; min-width: 0; height: 60rpx; padding: 0 20rpx; border-radius: 999rpx; color: #173b16; background: #f5f8ef; box-sizing: border-box; font-size: 24rpx; }
.bulk-bar { position: sticky; top: 0; z-index: 5; margin-top: 18rpx; padding: 18rpx; border-radius: 24rpx; background: #fff; box-shadow: 0 10rpx 26rpx rgba(73,83,47,.08); }
.bulk-left { display: flex; align-items: center; justify-content: space-between; gap: 16rpx; }
.select-all { width: 180rpx; height: 58rpx; line-height: 58rpx; border-radius: 999rpx; color: #2f6b23; background: #eef7e6; font-size: 24rpx; font-weight: 800; }
.selected-count { color: #60715c; font-size: 25rpx; font-weight: 800; }
.bulk-actions { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12rpx; margin-top: 16rpx; }
.bulk-btn, .bulk-more { height: 62rpx; line-height: 62rpx; border-radius: 999rpx; text-align: center; color: #fff; font-size: 23rpx; font-weight: 900; }
.bulk-btn.confirm { background: #2f6b23; }
.bulk-btn.delivering { background: #ef7d00; }
.bulk-more { background: #60715c; }
.sheet-head { display: flex; align-items: center; justify-content: space-between; }
.sheet-title { color: #173b16; font-size: 32rpx; font-weight: 900; }
.sheet-sub { margin-top: 8rpx; color: #60715c; font-size: 24rpx; }
.print-btn { width: 142rpx; height: 58rpx; line-height: 58rpx; border-radius: 999rpx; color: #fff; background: #2f6b23; font-size: 23rpx; }
.head, .item, .delivery-head { display: flex; justify-content: space-between; gap: 16rpx; }
.select-line { display: flex; align-items: center; min-width: 0; gap: 12rpx; }
.check-dot { flex: 0 0 auto; width: 38rpx; height: 38rpx; line-height: 38rpx; border: 2rpx solid #cfd8c8; border-radius: 50%; text-align: center; color: #fff; background: #fff; font-size: 24rpx; font-weight: 900; }
.check-dot.checked { border-color: #2f6b23; background: #2f6b23; }
.check-dot.disabled { border-color: #ddd; background: #eee; }
.order-no { color: #60715c; font-size: 25rpx; }
.status, .total { color: #df5d00; font-weight: 900; }
.info, .item { margin-top: 12rpx; color: #48613b; font-size: 25rpx; line-height: 1.5; }
.total { margin-top: 18rpx; text-align: right; font-size: 30rpx; }
.note { margin-top: 12rpx; padding: 12rpx 16rpx; border-radius: 14rpx; color: #df5d00; background: #fff3d2; font-size: 24rpx; }
.reissue-box { margin-top: 14rpx; padding: 14rpx 18rpx; border-radius: 14rpx; background: #eef7e6; }
.reissue-title { display: block; color: #2f6b23; font-size: 24rpx; font-weight: 900; }
.reissue-line { margin-top: 8rpx; color: #3d5a2f; font-size: 24rpx; line-height: 1.5; }
.delivery-total { margin-top: 16rpx; text-align: right; color: #173b16; font-size: 25rpx; font-weight: 800; }
.picker { margin-top: 18rpx; height: 68rpx; line-height: 68rpx; text-align: center; border-radius: 999rpx; color: #fff; background: #ef7d00; }
.select-all::after, .bulk-btn::after, .print-btn::after, .filter-mini::after { border: none; }
</style>
