<script setup>
import { onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { salesStats } from '../api'
import { isoDate, money, qtyText, statusLabel, statusTone } from '../utils/format'

const date = ref(isoDate())
const loading = ref(false)
const data = ref(null)

async function load() {
  loading.value = true
  try {
    data.value = await salesStats({ date: date.value })
  } catch (error) {
    ElMessage.error(error.message)
    data.value = null
  } finally {
    loading.value = false
  }
}

watch(date, load)
onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-toolbar">
      <span class="muted">统计口径：仅取消/关闭以外的订单计入金额，状态分布包含全部订单。</span>
      <div class="grow"></div>
      <el-date-picker v-model="date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" />
      <el-button :loading="loading" @click="load">刷新</el-button>
    </div>

    <el-row :gutter="14" v-loading="loading">
      <el-col :span="6"><el-card shadow="never"><div class="kpi">{{ data?.order_count ?? 0 }}</div><div class="muted">订单数</div></el-card></el-col>
      <el-col :span="6"><el-card shadow="never"><div class="kpi">¥{{ money(data?.estimated_total) }}</div><div class="muted">销售总额</div></el-card></el-col>
      <el-col :span="6"><el-card shadow="never"><div class="kpi">{{ qtyText(data?.total_quantity) }}</div><div class="muted">总数量</div></el-card></el-col>
      <el-col :span="6"><el-card shadow="never"><div class="kpi">{{ data?.item_kind_count ?? 0 }}</div><div class="muted">商品种类</div></el-card></el-col>
    </el-row>

    <div class="section-title">商品汇总</div>
    <el-table :data="data?.items || []" border>
      <el-table-column label="水果" prop="fruit_name" min-width="140" />
      <el-table-column label="规格" prop="spec" min-width="120" />
      <el-table-column label="单位" prop="unit" width="80" />
      <el-table-column label="数量" width="110">
        <template #default="{ row }">{{ qtyText(row.quantity) }}</template>
      </el-table-column>
      <el-table-column label="金额" width="120">
        <template #default="{ row }">¥{{ money(row.subtotal) }}</template>
      </el-table-column>
      <el-table-column label="涉及订单" prop="order_count" width="110" />
      <template #empty><span class="muted">该日期暂无销售数据</span></template>
    </el-table>

    <div class="section-title">状态分布</div>
    <el-table :data="data?.statuses || []" border>
      <el-table-column label="状态" min-width="140">
        <template #default="{ row }"><el-tag :type="statusTone(row.status)">{{ statusLabel(row.status) }}</el-tag></template>
      </el-table-column>
      <el-table-column label="订单数" prop="order_count" width="140" />
      <el-table-column label="金额" width="160">
        <template #default="{ row }">¥{{ money(row.amount) }}</template>
      </el-table-column>
      <template #empty><span class="muted">该日期暂无订单</span></template>
    </el-table>
  </div>
</template>

<style scoped>
.kpi {
  font-size: 24px;
  font-weight: 800;
}
</style>
