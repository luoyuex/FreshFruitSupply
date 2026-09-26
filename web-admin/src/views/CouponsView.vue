<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createCouponTemplate, grantCoupon, listCouponTemplates, listCustomers, updateCouponTemplate } from '../api'
import { COUPON_KINDS, dateText, money, statusLabel, statusTone } from '../utils/format'

const loading = ref(false)
const templates = ref([])
const customers = ref([])

const dialog = ref(false)
const saving = ref(false)
const form = reactive(blankTemplate())

const grantDialog = ref(false)
const granting = ref(false)
const grantForm = reactive({ customer_id: null, template_id: null })

function blankTemplate() {
  return {
    id: null,
    name: '',
    description: '',
    kind: 'discount',
    amount: 1,
    min_spend: 0,
    valid_days: 30,
    grant_on_verified: false,
    per_customer_limit: 1,
    is_active: true,
  }
}

const isReissue = computed(() => form.kind === 'reissue')
const activeTemplates = computed(() => templates.value.filter((item) => item.is_active))

async function load() {
  loading.value = true
  try {
    const [templateList, customerList] = await Promise.all([listCouponTemplates(), listCustomers().catch(() => [])])
    templates.value = templateList
    customers.value = customerList
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

function open(row) {
  Object.assign(form, row ? {
    ...row,
    amount: Number(row.amount),
    min_spend: Number(row.min_spend),
    description: row.description || '',
  } : blankTemplate())
  dialog.value = true
}

async function save() {
  if (!form.name.trim()) {
    ElMessage.warning('请填写券名称')
    return
  }
  if (!(Number(form.valid_days) > 0)) {
    ElMessage.warning('有效期天数必须大于 0')
    return
  }
  const payload = {
    name: form.name.trim(),
    description: form.description || null,
    kind: form.kind,
    amount: isReissue.value ? 0 : Number(form.amount),
    min_spend: isReissue.value ? 0 : Number(form.min_spend),
    valid_days: Number(form.valid_days),
    grant_on_verified: isReissue.value ? false : !!form.grant_on_verified,
    per_customer_limit: Number(form.per_customer_limit) || 1,
    is_active: !!form.is_active,
  }
  saving.value = true
  try {
    if (form.id) await updateCouponTemplate(form.id, payload)
    else await createCouponTemplate(payload)
    ElMessage.success('券种已保存')
    dialog.value = false
    await load()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    saving.value = false
  }
}

function openGrant(templateId = null) {
  grantForm.customer_id = null
  grantForm.template_id = templateId
  grantDialog.value = true
}

async function submitGrant() {
  if (!grantForm.customer_id) {
    ElMessage.warning('请选择客户')
    return
  }
  if (!grantForm.template_id) {
    ElMessage.warning('请选择券种')
    return
  }
  granting.value = true
  try {
    await grantCoupon(grantForm.customer_id, grantForm.template_id)
    ElMessage.success('已发券')
    grantDialog.value = false
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    granting.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-toolbar">
      <span class="muted">满减券参与实付计算、每单限用一张；补送券随单免费补配、可叠加多张、只能手动发放。</span>
      <div class="grow"></div>
      <el-button :disabled="!activeTemplates.length" @click="openGrant()">发券给用户</el-button>
      <el-button @click="load">刷新</el-button>
      <el-button type="primary" @click="open(null)">新增券种</el-button>
    </div>

    <el-table v-loading="loading" :data="templates" border>
      <el-table-column label="券种" min-width="200">
        <template #default="{ row }">
          <div>{{ row.name }}</div>
          <div class="muted">{{ row.description || '无说明' }}</div>
        </template>
      </el-table-column>
      <el-table-column label="类型" width="120">
        <template #default="{ row }">
          <el-tag :type="row.kind === 'reissue' ? 'warning' : 'primary'">{{ row.kind === 'reissue' ? '补送券' : '满减券' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="面额/门槛" min-width="150">
        <template #default="{ row }">
          <span v-if="row.kind === 'reissue'" class="muted">不涉及金额</span>
          <span v-else>减 ¥{{ money(row.amount) }}<span v-if="Number(row.min_spend) > 0"> · 满 ¥{{ money(row.min_spend) }}</span></span>
        </template>
      </el-table-column>
      <el-table-column label="有效期" width="100">
        <template #default="{ row }">{{ row.valid_days }} 天</template>
      </el-table-column>
      <el-table-column label="认证自动发放" width="130">
        <template #default="{ row }">
          <el-tag v-if="row.grant_on_verified" type="success" size="small">开启</el-tag>
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '启用中' : '已停用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="open(row)">编辑</el-button>
          <el-button size="small" type="primary" plain :disabled="!row.is_active" @click="openGrant(row.id)">发券</el-button>
        </template>
      </el-table-column>
      <template #empty><span class="muted">还没有券种，先新增一个</span></template>
    </el-table>

    <el-dialog v-model="dialog" :title="form.id ? '编辑券种' : '新增券种'" width="520px">
      <el-form label-width="110px">
        <el-form-item label="类型">
          <el-radio-group v-model="form.kind" :disabled="!!form.id && templates.find((t) => t.id === form.id)?.kind !== form.kind">
            <el-radio v-for="item in COUPON_KINDS" :key="item.value" :value="item.value">{{ item.label }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="isReissue ? '补送内容' : '券名称'" required>
          <el-input v-model="form.name" :placeholder="isReissue ? '如 补送-芒果1个' : '如 满100减10'" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
        <template v-if="!isReissue">
          <el-form-item label="面额" required>
            <el-input-number v-model="form.amount" :min="0.01" :precision="2" />
          </el-form-item>
          <el-form-item label="使用门槛">
            <el-input-number v-model="form.min_spend" :min="0" :precision="2" />
            <span class="muted hint">0 表示无门槛</span>
          </el-form-item>
          <el-form-item label="认证自动发放">
            <el-switch v-model="form.grant_on_verified" />
          </el-form-item>
        </template>
        <el-form-item label="有效天数" required>
          <el-input-number v-model="form.valid_days" :min="1" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="grantDialog" title="发券给用户" width="520px">
      <el-form label-width="90px">
        <el-form-item label="客户">
          <el-select v-model="grantForm.customer_id" filterable placeholder="按手机号/昵称/店铺搜索" style="width: 100%">
            <el-option
              v-for="item in customers"
              :key="item.id"
              :label="`${item.nickname || item.shop_name || '未命名'} · ${item.phone}`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="券种">
          <el-select v-model="grantForm.template_id" placeholder="选择启用中的券种" style="width: 100%">
            <el-option
              v-for="item in activeTemplates"
              :key="item.id"
              :label="`${item.name}（${item.kind === 'reissue' ? '补送券' : `减¥${money(item.amount)}`} · ${item.valid_days}天）`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <p class="muted note">发出去的券有效期从发放时刻起算，可在「用户管理 → 客户卡券」里查看与删除。</p>
      </el-form>
      <template #footer>
        <el-button @click="grantDialog = false">取消</el-button>
        <el-button type="primary" :loading="granting" @click="submitGrant">确认发券</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.hint,
.note {
  margin-left: 8px;
  font-size: 12px;
}

.note {
  margin: 0 0 0 90px;
}
</style>
