<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  bulkUpdateOrderStatus,
  deliverySheet,
  listOrderPayments,
  listOrders,
  refundOrder,
  resendOrderNotice,
  updateOrderStatus,
} from '../api'
import {
  ORDER_STATUSES,
  ORDER_TARGET_STATUSES,
  addressText,
  dateTimeSec,
  isoDate,
  money,
  noticeLabel,
  qtyText,
  shortDateTime,
  statusLabel,
  statusTone,
} from '../utils/format'

const activeTab = ref('list')
const date = ref(isoDate())
const status = ref('')
const keyword = ref('')
const loading = ref(false)
const orders = ref([])
const sheet = ref([])
const selection = ref([])
const tableRef = ref(null)

const drawerVisible = ref(false)
const currentOrder = ref(null)
const payments = ref([])
const paymentsLoading = ref(false)
const refunding = ref(false)
// 正在重发的通知，用「订单:类型」定位到具体那一个按钮
const resendingKey = ref('')

const filteredOrders = computed(() => {
  const word = keyword.value.trim().toLowerCase()
  if (!word) return orders.value
  return orders.value.filter((order) => (
    [order.order_no, order.receiver_name, order.receiver_phone, addressText(order)].join(' ').toLowerCase().includes(word)
  ))
})

const refundablePayments = computed(() => payments.value.filter((item) => item.status === 'success'))
const refundableAmount = computed(() => refundablePayments.value.reduce((sum, item) => sum + Number(item.amount), 0))

function queryParams() {
  const params = {}
  if (date.value) params.date = date.value
  return params
}

async function loadOrders() {
  loading.value = true
  try {
    orders.value = await listOrders({ ...queryParams(), ...(status.value ? { status: status.value } : {}) })
    selection.value = []
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

async function loadSheet() {
  loading.value = true
  try {
    sheet.value = await deliverySheet(queryParams())
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

async function reloadCurrentView() {
  if (activeTab.value === 'sheet') await loadSheet()
  else await loadOrders()
}

async function changeStatus(order, next) {
  const warning = next === 'cancelled' ? '已付款订单将原路退款、未付款订单将关闭。' : ''
  try {
    await ElMessageBox.confirm(`确认将订单 ${order.order_no} 改为「${statusLabel(next)}」？${warning}`, '修改状态', { type: 'warning' })
  } catch (error) {
    await loadOrders()
    return
  }
  try {
    await updateOrderStatus(order.id, next)
    ElMessage.success('状态已更新')
    await loadOrders()
  } catch (error) {
    ElMessage.error(error.message)
    await loadOrders()
  }
}

async function bulkTo(next) {
  const ids = selection.value.map((order) => order.id)
  if (!ids.length) {
    ElMessage.warning('请先勾选订单')
    return
  }
  const suffix = next === 'cancelled' ? '（已付款订单将原路退款）' : ''
  try {
    await ElMessageBox.confirm(`确认将选中的 ${ids.length} 笔订单改为「${statusLabel(next)}」${suffix}？`, '批量操作', { type: 'warning' })
  } catch (error) {
    return
  }
  try {
    await bulkUpdateOrderStatus(ids, next)
    ElMessage.success('批量更新完成')
    tableRef.value?.clearSelection()
    await loadOrders()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

async function openDrawer(order) {
  currentOrder.value = order
  drawerVisible.value = true
  await loadPayments()
}

async function loadPayments() {
  if (!currentOrder.value) return
  paymentsLoading.value = true
  try {
    payments.value = await listOrderPayments(currentOrder.value.id)
  } catch (error) {
    ElMessage.error(error.message)
    payments.value = []
  } finally {
    paymentsLoading.value = false
  }
}

async function doRefund(paymentId) {
  const targets = paymentId ? payments.value.filter((item) => item.id === paymentId) : refundablePayments.value
  const amount = targets.reduce((sum, item) => sum + Number(item.amount), 0)
  if (!targets.length) {
    ElMessage.warning('没有可退款的已支付流水')
    return
  }
  let reason = '后台退款'
  try {
    const input = await ElMessageBox.prompt(
      `将原路退回 ¥${money(amount)}（共 ${targets.length} 笔流水）。退款为受理制，到账以微信通知为准；此操作不会改变订单状态。`,
      '确认退款',
      { inputPlaceholder: '退款原因（选填，会显示在用户账单）', inputValue: '后台退款', type: 'warning' },
    )
    reason = (input.value || '').trim() || '后台退款'
  } catch (error) {
    return
  }
  refunding.value = true
  try {
    await refundOrder(currentOrder.value.id, { ...(paymentId ? { payment_id: paymentId } : {}), reason })
    ElMessage.success('退款已受理')
    await loadPayments()
    await loadOrders()
    // 抽屉头部的已付金额取自当前订单对象，重新指回列表里的新对象才会刷新
    const fresh = orders.value.find((item) => item.id === currentOrder.value?.id)
    if (fresh) currentOrder.value = fresh
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    refunding.value = false
  }
}

// 状态列要常驻：有失败就把每一封失败的都列出来（各自带重发），全成功只显示最近一封
function noticesToShow(order) {
  const notices = order.notifications || []
  const byTimeDesc = (list) => list.slice().sort((a, b) => String(b.updated_at || b.sent_at || '').localeCompare(String(a.updated_at || a.sent_at || '')))
  const failed = byTimeDesc(notices.filter((notice) => notice.status !== 'sent'))
  if (failed.length) return failed
  const sorted = byTimeDesc(notices)
  return sorted.length ? [sorted[0]] : []
}

function noticeSummary(notice) {
  if (notice.status === 'sent') return `${noticeLabel(notice.kind)}已发送 ${shortDateTime(notice.sent_at)}`
  return `${noticeLabel(notice.kind)}发送失败`
}

// 列表按订单预取要展示的通知，避免模板里对同一行反复排序
const visibleNotices = computed(() => {
  const map = {}
  for (const order of orders.value) map[order.id] = noticesToShow(order)
  return map
})

// 邮件按订单当前明细重建，改地址/加商品后再重发不会送出旧内容
async function doResend(order, kind) {
  resendingKey.value = `${order.id}:${kind}`
  try {
    await resendOrderNotice(order.id, kind)
    ElMessage.success(`${noticeLabel(kind)}已重发`)
    await loadOrders()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    resendingKey.value = ''
  }
}

async function copySheet() {
  const text = sheet.value.map((order) => (
    `${order.order_no} ${statusLabel(order.status)}\n${order.receiver_name} ${order.receiver_phone}\n${addressText(order)}\n` +
    `${(order.items || []).map((item) => `${item.fruit_name} ${item.spec} x${qtyText(item.quantity)}${item.unit}`).join('\n')}` +
    `${order.delivery_note ? `\n备注：${order.delivery_note}` : ''}`
  )).join('\n\n——\n\n')
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('送货单已复制')
  } catch (error) {
    ElMessage.error('复制失败，请手动选择表格内容')
  }
}

function summaryNumber(value) {
  return `¥${money(value)}`
}

watch(activeTab, (tab) => {
  if (tab === 'sheet') loadSheet()
  else loadOrders()
})
watch([date, status], reloadCurrentView)

onMounted(loadOrders)
</script>

<template>
  <div class="page">
    <div class="page-toolbar">
      <el-tabs v-model="activeTab" class="tabs">
        <el-tab-pane label="订单列表" name="list" />
        <el-tab-pane label="送货单" name="sheet" />
      </el-tabs>
      <div class="grow"></div>
      <el-date-picker v-model="date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" clearable />
      <el-button link type="primary" @click="date = isoDate()">今天</el-button>
      <el-button link type="primary" @click="date = ''">全部日期</el-button>
      <el-select v-if="activeTab === 'list'" v-model="status" placeholder="全部状态" clearable style="width: 140px">
        <el-option v-for="item in ORDER_STATUSES" :key="item" :label="statusLabel(item)" :value="item" />
      </el-select>
      <el-input v-if="activeTab === 'list'" v-model="keyword" placeholder="搜索订单号/收货人/电话/地址" clearable style="width: 240px" />
      <el-button :loading="loading" @click="reloadCurrentView">刷新</el-button>
    </div>

    <template v-if="activeTab === 'list'">
      <div class="page-toolbar">
        <span class="muted">已选 {{ selection.length }} 笔</span>
        <el-button type="success" plain :disabled="!selection.length" @click="bulkTo('confirmed')">批量确认</el-button>
        <el-button type="primary" plain :disabled="!selection.length" @click="bulkTo('delivering')">批量配送中</el-button>
        <el-button type="warning" plain :disabled="!selection.length" @click="bulkTo('completed')">批量完成</el-button>
        <el-button type="danger" plain :disabled="!selection.length" @click="bulkTo('cancelled')">批量取消并退款</el-button>
      </div>

      <el-table ref="tableRef" v-loading="loading" :data="filteredOrders" row-key="id" border @selection-change="selection = $event">
        <el-table-column type="selection" width="46" reserve-selection />
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="expand">
              <div v-for="item in row.items || []" :key="item.id" class="item-line">
                <span>{{ item.fruit_name }} · {{ item.spec }} · {{ qtyText(item.quantity) }}{{ item.unit }} × ¥{{ money(item.price) }}</span>
                <span>¥{{ money(item.subtotal) }}</span>
              </div>
              <div v-if="(row.reissue_coupons || []).length" class="item-line reissue">
                <span>本单补送</span>
                <span>{{ row.reissue_coupons.map((c) => c.name).join('、') }}</span>
              </div>
              <div v-if="row.delivery_note" class="item-line">
                <span>配送备注</span>
                <span>{{ row.delivery_note }}</span>
              </div>
              <div v-for="notice in row.notifications || []" :key="notice.kind" class="item-line notice-log">
                <span>{{ noticeLabel(notice.kind) }}</span>
                <span :class="{ 'danger-text': notice.status === 'failed' }">
                  {{ notice.status === 'sent' ? `已发送 · ${dateTimeSec(notice.sent_at)}` : `发送失败 · 已试 ${notice.attempts} 次` }}
                  <template v-if="notice.status === 'failed' && notice.error">（{{ notice.error }}）</template>
                </span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="订单" min-width="180">
          <template #default="{ row }">
            <div>{{ row.order_no }}</div>
            <div class="muted">{{ dateTimeSec(row.created_at) }}</div>
          </template>
        </el-table-column>
        <el-table-column label="收货人" min-width="140">
          <template #default="{ row }">
            <div>{{ row.receiver_name }}</div>
            <div class="muted">{{ row.receiver_phone }}</div>
          </template>
        </el-table-column>
        <el-table-column label="地址" min-width="220">
          <template #default="{ row }">{{ addressText(row) }}</template>
        </el-table-column>
        <el-table-column label="金额" min-width="170">
          <template #default="{ row }">
            <div>应付 <span class="money">{{ summaryNumber(row.payable_total) }}</span></div>
            <div class="muted">已付 {{ summaryNumber(row.paid_amount) }} · 原价 {{ summaryNumber(row.estimated_total) }}</div>
            <div v-if="Number(row.discount_amount) > 0" class="muted">优惠 ¥{{ money(row.discount_amount) }}</div>
            <div v-if="Number(row.delivery_fee) > 0" class="muted">配送费 ¥{{ money(row.delivery_fee) }}</div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="210">
          <template #default="{ row }">
            <el-tag :type="statusTone(row.status)">{{ statusLabel(row.status) }}</el-tag>
            <div
              v-for="notice in visibleNotices[row.id]"
              :key="notice.kind"
              class="notice-line"
              :class="{ 'danger-text': notice.status !== 'sent' }"
            >
              <el-tooltip
                :disabled="notice.status === 'sent'"
                :content="notice.error || '发送失败，原因未记录'"
                placement="top"
              >
                <span>{{ noticeSummary(notice) }}</span>
              </el-tooltip>
              <el-button
                v-if="notice.status !== 'sent'"
                link
                type="primary"
                size="small"
                :loading="resendingKey === `${row.id}:${notice.kind}`"
                @click="doResend(row, notice.kind)"
              >
                重发
              </el-button>
            </div>
            <div v-if="!visibleNotices[row.id].length" class="muted notice-line">未触发邮件</div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="230" fixed="right">
          <template #default="{ row }">
            <el-select
              :model-value="row.status"
              size="small"
              style="width: 118px"
              @update:model-value="(value) => value !== row.status && changeStatus(row, value)"
            >
              <el-option v-for="item in ORDER_TARGET_STATUSES" :key="item" :label="statusLabel(item)" :value="item" />
            </el-select>
            <el-button size="small" type="danger" plain :disabled="!(Number(row.paid_amount) > 0)" @click="openDrawer(row)">
              退款
            </el-button>
          </template>
        </el-table-column>
        <template #empty>
          <span class="muted">当前筛选条件下没有订单</span>
        </template>
      </el-table>
    </template>

    <template v-else>
      <div class="page-toolbar">
        <span class="muted">送货单为待确认 / 已确认 / 配送中的订单，可直接截图或复制发给配送。</span>
        <div class="grow"></div>
        <el-button :disabled="!sheet.length" @click="copySheet">复制送货单</el-button>
      </div>
      <el-table v-loading="loading" :data="sheet" border>
        <el-table-column label="订单" width="170">
          <template #default="{ row }">
            <div>{{ row.order_no }}</div>
            <div class="muted">{{ dateTimeSec(row.created_at) }}</div>
          </template>
        </el-table-column>
        <el-table-column label="收货人" width="150">
          <template #default="{ row }">
            <div>{{ row.receiver_name }}</div>
            <div class="muted">{{ row.receiver_phone }}</div>
          </template>
        </el-table-column>
        <el-table-column label="地址" min-width="200">
          <template #default="{ row }">{{ addressText(row) }}</template>
        </el-table-column>
        <el-table-column label="商品明细" min-width="260">
          <template #default="{ row }">
            <div v-for="item in row.items || []" :key="item.id">{{ item.fruit_name }} {{ item.spec }} × {{ qtyText(item.quantity) }}{{ item.unit }}</div>
            <div v-if="(row.reissue_coupons || []).length" class="reissue">补送：{{ row.reissue_coupons.map((c) => c.name).join('、') }}</div>
          </template>
        </el-table-column>
        <el-table-column label="备注" min-width="140">
          <template #default="{ row }">{{ row.delivery_note || '—' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }"><el-tag :type="statusTone(row.status)">{{ statusLabel(row.status) }}</el-tag></template>
        </el-table-column>
        <template #empty><span class="muted">该日期没有待配送订单</span></template>
      </el-table>
    </template>

    <el-drawer v-model="drawerVisible" :title="`支付与退款 · ${currentOrder?.order_no || ''}`" size="620px">
      <div v-loading="paymentsLoading">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="应付">¥{{ money(currentOrder?.payable_total) }}</el-descriptions-item>
          <el-descriptions-item label="已付">¥{{ money(currentOrder?.paid_amount) }}</el-descriptions-item>
        </el-descriptions>
        <div class="page-toolbar drawer-actions">
          <span class="muted">仅「已支付」流水可退，可退合计 <span class="money">¥{{ money(refundableAmount) }}</span></span>
          <div class="grow"></div>
          <el-button type="danger" :disabled="!refundableAmount" :loading="refunding" @click="doRefund(null)">
            全部退款
          </el-button>
        </div>
        <el-table :data="payments" border size="small">
          <el-table-column label="商户单号" prop="out_trade_no" min-width="180" />
          <el-table-column label="类型" width="90">
            <template #default="{ row }">{{ row.kind === 'initial' ? '首付' : '补差价' }}</template>
          </el-table-column>
          <el-table-column label="金额" width="90">
            <template #default="{ row }">¥{{ money(row.amount) }}</template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }"><el-tag :type="statusTone(row.status)">{{ statusLabel(row.status) }}</el-tag></template>
          </el-table-column>
          <el-table-column label="时间" min-width="150">
            <template #default="{ row }">{{ dateTimeSec(row.paid_at || row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="90">
            <template #default="{ row }">
              <el-button v-if="row.status === 'success'" size="small" type="danger" plain :loading="refunding" @click="doRefund(row.id)">
                退款
              </el-button>
              <span v-else class="muted">—</span>
            </template>
          </el-table-column>
          <template #empty><span class="muted">该订单还没有支付流水</span></template>
        </el-table>
        <p class="muted tip">
          退款只把钱原路退回，不会改变订单状态；若要连同取消订单，请在列表把状态改为「已取消」。
          同一笔退款两次发起需间隔 1 分钟以上。
        </p>
      </div>
    </el-drawer>
  </div>
</template>

<style scoped>
.tabs {
  margin-bottom: -14px;
}

.expand {
  padding: 6px 46px;
}

.notice-line {
  margin-top: 4px;
  font-size: 12px;
}

.reissue {
  color: #ff6a00;
}

.drawer-actions {
  margin-top: 14px;
}

.tip {
  margin-top: 12px;
  font-size: 12px;
  line-height: 1.7;
}
</style>
