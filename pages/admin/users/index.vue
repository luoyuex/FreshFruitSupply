<script setup>
import { computed, onMounted, reactive, shallowRef } from 'vue'
import { onPullDownRefresh } from '@dcloudio/uni-app'
import { request } from '../../../utils/request.js'
import { statusLabel, shortDateTime } from '../../../utils/format.js'
import { goAdminNav, redirectIfNoPermission, visibleAdminNavItems } from '../../../utils/admin.js'

const admins = shallowRef([])
const customers = shallowRef([])
const templates = shallowRef([])
const loading = shallowRef(false)
const saving = shallowRef(false)
const activeTab = shallowRef('admins')
const adminModalVisible = shallowRef(false)
const passwordModalVisible = shallowRef(false)
const editingAdminId = shallowRef(null)
const passwordAdminId = shallowRef(null)
// 发券给客户（补偿）
const grantVisible = shallowRef(false)
const granting = shallowRef(false)
const grantCustomer = shallowRef(null)
const activeTemplates = computed(() => templates.value.filter((item) => item.is_active))
const roleOptions = [
  { value: 'super_admin', label: '超级管理员' },
  { value: 'order_admin', label: '订单管理员' },
]
const navItems = computed(() => visibleAdminNavItems())
const roleNames = computed(() => roleOptions.map((item) => item.label))
const rolePickerIndex = computed(() => Math.max(0, roleOptions.findIndex((item) => item.value === adminForm.role)))
const adminOpenids = computed(() => new Set(admins.value.map((item) => item.wechat_openid).filter(Boolean)))
const adminForm = reactive({ username: '', password: '', role: 'order_admin', wechat_openid: '', nickname: '', is_active: true })
const passwordForm = reactive({ password: '' })

function roleLabel(role) {
  return roleOptions.find((item) => item.value === role)?.label || role
}

async function loadAll() {
  if (redirectIfNoPermission('users')) return
  loading.value = true
  try {
    const [adminRows, customerRows, templateRows] = await Promise.all([
      request({ url: '/admin/admin-users', admin: true }),
      request({ url: '/admin/customers', admin: true }),
      request({ url: '/admin/coupon-templates', admin: true }),
    ])
    admins.value = adminRows
    customers.value = customerRows
    templates.value = templateRows
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
    if (err.message.includes('token') || err.message.includes('Missing')) {
      uni.redirectTo({ url: '/pages/admin/login/index' })
    } else if (err.message.includes('permission') || err.message.includes('权限')) {
      uni.redirectTo({ url: '/pages/admin/orders/index' })
    }
  } finally {
    loading.value = false
  }
}

function resetAdminForm() {
  editingAdminId.value = null
  Object.assign(adminForm, { username: '', password: '', role: 'order_admin', wechat_openid: '', nickname: '', is_active: true })
}

function openAdminModal(admin = null) {
  resetAdminForm()
  if (admin) {
    editingAdminId.value = admin.id
    Object.assign(adminForm, {
      username: admin.username,
      password: '',
      role: admin.role,
      wechat_openid: admin.wechat_openid || '',
      nickname: admin.nickname || '',
      is_active: admin.is_active,
    })
  }
  adminModalVisible.value = true
}

function openCustomerAdminModal(customer) {
  if (!customer.wechat_openid) {
    uni.showToast({ title: '该客户没有微信 openid', icon: 'none' })
    return
  }
  if (adminOpenids.value.has(customer.wechat_openid)) {
    uni.showToast({ title: '该微信已是管理员', icon: 'none' })
    return
  }
  resetAdminForm()
  Object.assign(adminForm, {
    username: customer.phone && !customer.phone.startsWith('wx:') ? customer.phone : `wx${customer.id}`,
    password: '',
    role: 'order_admin',
    wechat_openid: customer.wechat_openid,
    nickname: customer.nickname || customer.shop_name || customer.contact_name || '',
    is_active: true,
  })
  adminModalVisible.value = true
}

function isCustomerAdmin(customer) {
  return Boolean(customer.wechat_openid && adminOpenids.value.has(customer.wechat_openid))
}

function openGrant(customer) {
  if (!activeTemplates.value.length) {
    uni.showToast({ title: '暂无启用中的券种', icon: 'none' })
    return
  }
  grantCustomer.value = customer
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

function closeAdminModal() {
  adminModalVisible.value = false
  resetAdminForm()
}

function changeRole(event) {
  adminForm.role = roleOptions[event.detail.value]?.value || 'order_admin'
}

async function saveAdmin() {
  if (!adminForm.username.trim()) {
    uni.showToast({ title: '请填写账号', icon: 'none' })
    return
  }
  if (!editingAdminId.value && !adminForm.password) {
    uni.showToast({ title: '请填写初始密码', icon: 'none' })
    return
  }
  saving.value = true
  const url = editingAdminId.value ? `/admin/admin-users/${editingAdminId.value}` : '/admin/admin-users'
  const method = editingAdminId.value ? 'PATCH' : 'POST'
  try {
    const payload = { ...adminForm, username: adminForm.username.trim(), wechat_openid: adminForm.wechat_openid.trim(), nickname: adminForm.nickname.trim() }
    if (editingAdminId.value) delete payload.password
    await request({ url, method, admin: true, data: payload })
    uni.showToast({ title: '管理员已保存', icon: 'success' })
    closeAdminModal()
    await loadAll()
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
  } finally {
    saving.value = false
  }
}

function openPasswordModal(admin) {
  passwordAdminId.value = admin.id
  passwordForm.password = ''
  passwordModalVisible.value = true
}

function closePasswordModal() {
  passwordModalVisible.value = false
  passwordAdminId.value = null
  passwordForm.password = ''
}

async function resetPassword() {
  if (!passwordForm.password || passwordForm.password.length < 6) {
    uni.showToast({ title: '密码至少6位', icon: 'none' })
    return
  }
  saving.value = true
  try {
    await request({ url: `/admin/admin-users/${passwordAdminId.value}/password`, method: 'PATCH', admin: true, data: { password: passwordForm.password } })
    uni.showToast({ title: '密码已重置', icon: 'success' })
    closePasswordModal()
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
  } finally {
    saving.value = false
  }
}

onMounted(loadAll)

onPullDownRefresh(async () => {
  try {
    await loadAll()
  } finally {
    uni.stopPullDownRefresh()
  }
})
</script>

<template>
  <view class="page">
    <view class="admin-nav">
      <button v-for="item in navItems" :key="item.key" class="nav-button" :class="{ active: item.key === 'users' }" @tap="goAdminNav(item)">{{ item.label }}</button>
    </view>

    <view class="tabs">
      <button class="tab" :class="{ active: activeTab === 'admins' }" @tap="activeTab = 'admins'">管理员账号</button>
      <button class="tab" :class="{ active: activeTab === 'customers' }" @tap="activeTab = 'customers'">客户用户</button>
    </view>

    <view v-if="loading" class="empty">正在加载用户...</view>

    <template v-if="activeTab === 'admins'">
      <view class="section-head">
        <view>
          <view class="section-title">管理员账号</view>
          <view class="section-sub">绑定微信 openid 后，该用户个人中心才显示后台入口。</view>
        </view>
        <button class="add-btn" @tap="openAdminModal()">新增</button>
      </view>
      <view v-for="admin in admins" :key="admin.id" class="card">
        <view class="card-head">
          <view>
            <view class="name">{{ admin.nickname || admin.username }}</view>
            <view class="meta">{{ admin.username }} · {{ roleLabel(admin.role) }}</view>
          </view>
          <text class="status" :class="{ off: !admin.is_active }">{{ admin.is_active ? '启用' : '停用' }}</text>
        </view>
        <view class="info">微信 openid：{{ admin.wechat_openid || '未绑定' }}</view>
        <view class="actions">
          <button class="action" @tap="openAdminModal(admin)">编辑</button>
          <button class="action ghost" @tap="openPasswordModal(admin)">重置密码</button>
        </view>
      </view>
    </template>

    <template v-else>
      <view class="section-head">
        <view>
          <view class="section-title">客户用户</view>
          <view class="section-sub">查看客户微信、认证和订单概览，可直接把客户微信设为后台管理员。</view>
        </view>
      </view>
      <view v-for="customer in customers" :key="customer.id" class="card">
        <view class="card-head">
          <view>
            <view class="name">{{ customer.nickname || customer.shop_name || customer.phone }}</view>
            <view class="meta">{{ customer.phone }} · {{ statusLabel(customer.verification_status) }}</view>
          </view>
          <text class="status">{{ customer.order_count }}单</text>
        </view>
        <view class="info">微信 openid：{{ customer.wechat_openid || '无' }}</view>
        <view class="info">联系人：{{ customer.contact_name || '-' }} · {{ customer.business_type || '-' }}</view>
        <view class="info">最近下单：{{ shortDateTime(customer.latest_order_at) || '-' }}</view>
        <view class="actions">
          <button class="action" @tap="openGrant(customer)">发券</button>
          <button
            class="action"
            :class="{ ghost: isCustomerAdmin(customer) || !customer.wechat_openid }"
            :disabled="isCustomerAdmin(customer) || !customer.wechat_openid"
            @tap="openCustomerAdminModal(customer)"
          >
            {{ isCustomerAdmin(customer) ? '已开通后台入口' : '设为管理员' }}
          </button>
        </view>
      </view>
    </template>

    <view v-if="adminModalVisible" class="modal-mask" @tap="closeAdminModal">
      <view class="modal-card" @tap.stop>
        <view class="modal-title">{{ editingAdminId ? '编辑管理员' : '新增管理员' }}</view>
        <input v-model="adminForm.username" class="input" placeholder="登录账号" />
        <input v-if="!editingAdminId" v-model="adminForm.password" class="input" password placeholder="初始密码，至少6位" />
        <picker :range="roleNames" :value="rolePickerIndex" @change="changeRole">
          <view class="picker">角色：{{ roleLabel(adminForm.role) }}</view>
        </picker>
        <input v-model="adminForm.nickname" class="input" placeholder="昵称，可不填" />
        <input v-model="adminForm.wechat_openid" class="input" placeholder="绑定微信 openid，可不填" />
        <view class="switch-row">
          <text>启用账号</text>
          <switch :checked="adminForm.is_active" @change="adminForm.is_active = $event.detail.value" />
        </view>
        <button class="save" :loading="saving" @tap="saveAdmin">保存</button>
      </view>
    </view>

    <view v-if="passwordModalVisible" class="modal-mask" @tap="closePasswordModal">
      <view class="modal-card" @tap.stop>
        <view class="modal-title">重置密码</view>
        <input v-model="passwordForm.password" class="input" password placeholder="新密码，至少6位" />
        <button class="save" :loading="saving" @tap="resetPassword">确认重置</button>
      </view>
    </view>

    <coupon-grant-modal
      :visible="grantVisible"
      :templates="activeTemplates"
      :customer="grantCustomer"
      :saving="granting"
      @close="grantVisible = false"
      @confirm="handleGrant"
    />
  </view>
</template>

<style scoped>
.page { min-height: 100vh; padding: 24rpx; background: #f5f8ef; box-sizing: border-box; }
.admin-nav, .tabs, .actions { display: flex; gap: 10rpx; }
.nav-button, .tab { flex: 1; height: 68rpx; line-height: 68rpx; border-radius: 999rpx; color: #2f4b21; background: #fff; font-size: 24rpx; }
.nav-button.active, .tab.active { color: #fff; background: #2f6b23; }
.tabs { margin-top: 18rpx; }
.section-head, .card, .empty { margin-top: 18rpx; padding: 24rpx; border-radius: 26rpx; background: #fff; box-shadow: 0 10rpx 26rpx rgba(73,83,47,.08); }
.section-head { display: flex; align-items: center; justify-content: space-between; gap: 18rpx; }
.section-title { color: #173b16; font-size: 31rpx; font-weight: 900; }
.section-sub, .meta, .info { margin-top: 8rpx; color: #60715c; font-size: 24rpx; line-height: 1.45; }
.add-btn, .action, .save { border-radius: 999rpx; color: #fff; background: #2f6b23; font-size: 24rpx; font-weight: 800; }
.add-btn { flex-shrink: 0; width: 118rpx; height: 58rpx; line-height: 58rpx; }
.card-head { display: flex; justify-content: space-between; gap: 18rpx; }
.name { color: #173b16; font-size: 29rpx; font-weight: 900; }
.status { flex-shrink: 0; color: #df5d00; font-size: 24rpx; font-weight: 900; }
.status.off { color: #999; }
.actions { margin-top: 18rpx; }
.action { flex: 1; height: 62rpx; line-height: 62rpx; }
.action.ghost { color: #2f6b23; background: #eef7e6; }
.action[disabled] { color: #8a9784; background: #eef1ea; }
.empty { text-align: center; color: #768273; font-size: 26rpx; }
.modal-mask { position: fixed; z-index: 99; left: 0; right: 0; top: 0; bottom: 0; display: flex; align-items: flex-end; background: rgba(16, 28, 12, .45); }
.modal-card { width: 100%; padding: 30rpx 28rpx calc(54rpx + env(safe-area-inset-bottom)); border-radius: 34rpx 34rpx 0 0; background: #fff; box-sizing: border-box; }
.modal-title { color: #173b16; font-size: 34rpx; font-weight: 900; }
.input, .picker { width: 100%; min-height: 76rpx; margin-top: 16rpx; padding: 0 22rpx; border-radius: 18rpx; color: #48613b; background: #f5f8ef; font-size: 26rpx; box-sizing: border-box; }
.picker { display: flex; align-items: center; }
.switch-row { display: flex; align-items: center; justify-content: space-between; margin-top: 18rpx; color: #48613b; font-size: 26rpx; }
.save { margin-top: 24rpx; height: 76rpx; line-height: 76rpx; }
.add-btn::after, .action::after, .save::after, .nav-button::after, .tab::after { border: none; }
</style>
