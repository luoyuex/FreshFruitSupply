<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createAdminUser,
  deleteCustomerCoupon,
  grantCoupon,
  listAdminUsers,
  listCouponTemplates,
  listCustomerCoupons,
  listCustomers,
  resetAdminPassword,
  updateAdminUser,
} from '../api'
import { dateText, dateTimeSec, money, roleLabel, statusLabel, statusTone } from '../utils/format'

const activeTab = ref('admins')
const loading = ref(false)
const admins = ref([])
const customers = ref([])
const templates = ref([])
const keyword = ref('')

const dialog = ref(false)
const saving = ref(false)
const form = reactive(blankAdmin())

const drawer = ref(false)
const currentCustomer = ref(null)
const coupons = ref([])
const couponsLoading = ref(false)
const grantTemplateId = ref(null)

function blankAdmin() {
  return { id: null, username: '', password: '', role: 'order_admin', nickname: '', wechat_openid: '', is_active: true }
}

const filteredCustomers = computed(() => {
  const word = keyword.value.trim().toLowerCase()
  if (!word) return customers.value
  return customers.value.filter((item) => (
    [item.phone, item.nickname, item.shop_name, item.contact_name, item.wechat_openid].join(' ').toLowerCase().includes(word)
  ))
})

const activeTemplates = computed(() => templates.value.filter((item) => item.is_active))

function adminByOpenid(openid) {
  if (!openid) return null
  return admins.value.find((item) => item.wechat_openid === openid) || null
}

async function load() {
  loading.value = true
  try {
    const tasks = activeTab.value === 'admins'
      ? [listAdminUsers(), listCustomers(), listCouponTemplates()]
      : [Promise.resolve(admins.value.length ? admins.value : []), listCustomers(), listCouponTemplates()]
    const [adminList, customerList, templateList] = await Promise.all(tasks)
    admins.value = adminList
    customers.value = customerList
    templates.value = templateList
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

function openAdmin(row, prefill = null) {
  Object.assign(form, row ? { ...row, password: '' } : { ...blankAdmin(), ...(prefill || {}) })
  dialog.value = true
}

async function saveAdmin() {
  if (!form.username.trim()) {
    ElMessage.warning('用户名必填')
    return
  }
  if (!form.id && !form.password) {
    ElMessage.warning('新增管理员必须设置密码')
    return
  }
  if (form.password && form.password.length < 6) {
    ElMessage.warning('密码至少 6 位')
    return
  }
  const payload = {
    username: form.username.trim(),
    role: form.role,
    nickname: form.nickname || null,
    wechat_openid: form.wechat_openid || null,
    is_active: !!form.is_active,
  }
  if (form.password) payload.password = form.password
  saving.value = true
  try {
    if (form.id) await updateAdminUser(form.id, payload)
    else await createAdminUser(payload)
    ElMessage.success('已保存')
    dialog.value = false
    await load()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    saving.value = false
  }
}

async function resetPassword(row) {
  let password
  try {
    const input = await ElMessageBox.prompt(`为「${row.username}」设置新密码`, '重置密码', {
      inputPlaceholder: '至少 6 位',
      inputValidator: (value) => (value && value.length >= 6 ? true : '密码至少 6 位'),
    })
    password = input.value
  } catch (error) {
    return
  }
  try {
    await resetAdminPassword(row.id, password)
    ElMessage.success('密码已重置')
  } catch (error) {
    ElMessage.error(error.message)
  }
}

async function promote(customer) {
  if (!customer.wechat_openid) {
    ElMessage.warning('该客户没有微信 openid，无法绑定后台入口')
    return
  }
  if (adminByOpenid(customer.wechat_openid)) {
    ElMessage.info('该微信已是管理员')
    return
  }
  Object.assign(form, blankAdmin())
  form.username = customer.phone || `admin_${customer.id}`
  form.nickname = customer.nickname || customer.shop_name || ''
  form.wechat_openid = customer.wechat_openid
  dialog.value = true
}

async function openCoupons(customer) {
  currentCustomer.value = customer
  drawer.value = true
  grantTemplateId.value = null
  await loadCoupons()
}

async function loadCoupons() {
  if (!currentCustomer.value) return
  couponsLoading.value = true
  try {
    coupons.value = await listCustomerCoupons(currentCustomer.value.id)
  } catch (error) {
    ElMessage.error(error.message)
    coupons.value = []
  } finally {
    couponsLoading.value = false
  }
}

async function submitGrant() {
  if (!grantTemplateId.value) {
    ElMessage.warning('请选择券种')
    return
  }
  try {
    await grantCoupon(currentCustomer.value.id, grantTemplateId.value)
    ElMessage.success('已发券')
    grantTemplateId.value = null
    await loadCoupons()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

async function removeCoupon(coupon) {
  try {
    await ElMessageBox.confirm(`确认删除「${coupon.name}」？删除不可恢复，且不影响历史订单实付。`, '删除卡券', { type: 'warning' })
  } catch (error) {
    return
  }
  try {
    await deleteCustomerCoupon(currentCustomer.value.id, coupon.id)
    ElMessage.success('已删除')
    await loadCoupons()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-toolbar">
      <el-tabs v-model="activeTab" class="tabs" @tab-change="load">
        <el-tab-pane label="后台管理员" name="admins" />
        <el-tab-pane label="客户用户" name="customers" />
      </el-tabs>
      <div class="grow"></div>
      <el-input v-if="activeTab === 'customers'" v-model="keyword" placeholder="搜索手机号/昵称/店铺/openid" clearable style="width: 260px" />
      <el-button @click="load">刷新</el-button>
      <el-button v-if="activeTab === 'admins'" type="primary" @click="openAdmin(null)">新增管理员</el-button>
    </div>

    <el-table v-if="activeTab === 'admins'" v-loading="loading" :data="admins" border>
      <el-table-column label="用户名" prop="username" min-width="150" />
      <el-table-column label="昵称" prop="nickname" min-width="120" />
      <el-table-column label="角色" width="130">
        <template #default="{ row }"><el-tag :type="row.role === 'super_admin' ? 'danger' : 'primary'">{{ roleLabel(row.role) }}</el-tag></template>
      </el-table-column>
      <el-table-column label="绑定微信 openid" min-width="220">
        <template #default="{ row }"><span :class="row.wechat_openid ? '' : 'muted'">{{ row.wechat_openid || '未绑定' }}</span></template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }"><el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '启用' : '停用' }}</el-tag></template>
      </el-table-column>
      <el-table-column label="创建时间" width="180">
        <template #default="{ row }">{{ dateTimeSec(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openAdmin(row)">编辑</el-button>
          <el-button size="small" type="warning" plain @click="resetPassword(row)">重置密码</el-button>
        </template>
      </el-table-column>
      <template #empty><span class="muted">还没有管理员账号</span></template>
    </el-table>

    <el-table v-else v-loading="loading" :data="filteredCustomers" border>
      <el-table-column label="客户" min-width="180">
        <template #default="{ row }">
          <div>{{ row.nickname || row.shop_name || '未命名' }}</div>
          <div class="muted">{{ row.phone }}</div>
        </template>
      </el-table-column>
      <el-table-column label="店铺/联系人" min-width="160">
        <template #default="{ row }">
          <div>{{ row.shop_name || '—' }}</div>
          <div class="muted">{{ row.contact_name || '' }} {{ row.business_type || '' }}</div>
        </template>
      </el-table-column>
      <el-table-column label="认证" width="100">
        <template #default="{ row }"><el-tag :type="statusTone(row.verification_status)">{{ statusLabel(row.verification_status) }}</el-tag></template>
      </el-table-column>
      <el-table-column label="订单数" prop="order_count" width="90" />
      <el-table-column label="最近下单" width="160">
        <template #default="{ row }">{{ row.latest_order_at ? dateText(row.latest_order_at) : '—' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="230" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openCoupons(row)">卡券</el-button>
          <el-button
            size="small"
            type="primary"
            plain
            :disabled="!row.wechat_openid || !!adminByOpenid(row.wechat_openid)"
            @click="promote(row)"
          >
            {{ adminByOpenid(row.wechat_openid) ? '已开通后台' : '设为管理员' }}
          </el-button>
        </template>
      </el-table-column>
      <template #empty><span class="muted">暂无客户</span></template>
    </el-table>

    <el-dialog v-model="dialog" :title="form.id ? '编辑管理员' : '新增管理员'" width="520px">
      <el-form label-width="120px">
        <el-form-item label="用户名" required>
          <el-input v-model="form.username" :disabled="!!form.id" placeholder="登录账号" />
        </el-form-item>
        <el-form-item :label="form.id ? '重置密码' : '初始密码'" :required="!form.id">
          <el-input v-model="form.password" type="password" show-password :placeholder="form.id ? '留空表示不修改' : '至少 6 位'" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role" style="width: 100%">
            <el-option label="超级管理员（全部模块）" value="super_admin" />
            <el-option label="订单管理员（仅订单）" value="order_admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="form.nickname" placeholder="选填" />
        </el-form-item>
        <el-form-item label="微信 openid">
          <el-input v-model="form.wechat_openid" placeholder="绑定后该微信在小程序才显示后台入口" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveAdmin">保存</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="drawer" :title="`客户卡券 · ${currentCustomer?.nickname || currentCustomer?.phone || ''}`" size="620px">
      <div class="page-toolbar">
        <el-select v-model="grantTemplateId" placeholder="选择券种" clearable style="width: 260px" size="small">
          <el-option
            v-for="item in activeTemplates"
            :key="item.id"
            :label="`${item.name}（${item.kind === 'reissue' ? '补送券' : `减¥${money(item.amount)}`}）`"
            :value="item.id"
          />
        </el-select>
        <el-button size="small" type="primary" :disabled="!activeTemplates.length" @click="submitGrant">发券</el-button>
      </div>
      <el-table v-loading="couponsLoading" :data="coupons" border size="small">
        <el-table-column label="券名" min-width="150">
          <template #default="{ row }">
            <div>{{ row.name }}</div>
            <div class="muted">{{ row.source === 'admin' ? '后台发放' : '认证发放' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="面额/门槛" width="130">
          <template #default="{ row }">
            <span v-if="row.kind === 'reissue'" class="muted">补送</span>
            <span v-else>¥{{ money(row.amount) }}<span v-if="Number(row.min_spend) > 0">/满{{ money(row.min_spend) }}</span></span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }"><el-tag :type="statusTone(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag></template>
        </el-table-column>
        <el-table-column label="到期" width="120">
          <template #default="{ row }">{{ dateText(row.expires_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button size="small" type="danger" plain @click="removeCoupon(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty><span class="muted">该客户还没有卡券</span></template>
      </el-table>
    </el-drawer>
  </div>
</template>

<style scoped>
.tabs {
  margin-bottom: -14px;
}
</style>
