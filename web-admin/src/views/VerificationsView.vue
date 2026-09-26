<script setup>
import { onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listVerifications, revokeVerification } from '../api'
import { dateTimeSec, statusLabel, statusTone } from '../utils/format'

const status = ref('')
const loading = ref(false)
const rows = ref([])

async function load() {
  loading.value = true
  try {
    rows.value = await listVerifications(status.value ? { status: status.value } : {})
  } catch (error) {
    ElMessage.error(error.message)
    rows.value = []
  } finally {
    loading.value = false
  }
}

async function revoke(row) {
  try {
    await ElMessageBox.confirm(
      `确认取消「${row.shop_name}」的认证资格？取消后该客户按普通价下单，可重新提交认证。`,
      '取消认证',
      { type: 'warning', confirmButtonText: '确认取消认证', confirmButtonClass: 'el-button--danger' },
    )
  } catch (error) {
    return
  }
  try {
    await revokeVerification(row.id, { status: 'revoked', review_note: '认证资料需要重新提交' })
    ElMessage.success('已取消认证')
    await load()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

watch(status, load)
onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-toolbar">
      <span class="muted">客户提交认证后自动生效，这里仅支持取消当前有效的认证。</span>
      <div class="grow"></div>
      <el-select v-model="status" placeholder="全部状态" clearable style="width: 150px">
        <el-option label="已认证" value="verified" />
        <el-option label="待审核" value="pending_review" />
        <el-option label="未通过" value="rejected" />
        <el-option label="已取消" value="revoked" />
      </el-select>
      <el-button :loading="loading" @click="load">刷新</el-button>
    </div>

    <el-table v-loading="loading" :data="rows" border>
      <el-table-column label="店铺" min-width="170">
        <template #default="{ row }">
          <div>{{ row.shop_name }}</div>
          <div class="muted">{{ row.contact_name }} · {{ row.phone }}</div>
        </template>
      </el-table-column>
      <el-table-column label="经营类型" prop="business_type" min-width="120" />
      <el-table-column label="资料图片" min-width="200">
        <template #default="{ row }">
          <el-image
            v-for="url in row.image_urls || []"
            :key="url"
            :src="url"
            :preview-src-list="row.image_urls || []"
            :initial-index="(row.image_urls || []).indexOf(url)"
            fit="cover"
            preview-teleported
            class="thumb"
          />
          <span v-if="!(row.image_urls || []).length" class="muted">无</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="110">
        <template #default="{ row }"><el-tag :type="statusTone(row.status)">{{ statusLabel(row.status) }}</el-tag></template>
      </el-table-column>
      <el-table-column label="提交时间" min-width="150">
        <template #default="{ row }">{{ dateTimeSec(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="备注" prop="review_note" min-width="140" />
      <el-table-column label="操作" width="130" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 'verified'" size="small" type="danger" plain @click="revoke(row)">取消认证</el-button>
          <span v-else class="muted">客户可重新提交</span>
        </template>
      </el-table-column>
      <template #empty><span class="muted">暂无认证申请</span></template>
    </el-table>
  </div>
</template>

<style scoped>
.thumb {
  width: 54px;
  height: 54px;
  margin-right: 6px;
  border-radius: 6px;
}
</style>
