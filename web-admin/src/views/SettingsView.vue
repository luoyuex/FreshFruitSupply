<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getDeliveryConfig, updateDeliveryConfig } from '../api'
import { money } from '../utils/format'

const loading = ref(false)
const saving = ref(false)
const form = reactive({ free_threshold: 0, fee: 0 })

const preview = computed(() => `满 ¥${money(form.free_threshold)} 包邮，否则收配送费 ¥${money(form.fee)}`)

async function load() {
  loading.value = true
  try {
    const data = await getDeliveryConfig()
    form.free_threshold = Number(data.free_threshold)
    form.fee = Number(data.fee)
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  try {
    const data = await updateDeliveryConfig({ free_threshold: Number(form.free_threshold), fee: Number(form.fee) })
    form.free_threshold = Number(data.free_threshold)
    form.fee = Number(data.fee)
    ElMessage.success('已保存')
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <el-card shadow="never" v-loading="loading" class="card">
      <template #header>配送费设置</template>
      <el-form label-width="130px">
        <el-form-item label="包邮门槛">
          <el-input-number v-model="form.free_threshold" :min="0" :precision="2" />
          <span class="muted hint">订单原价达到该金额免收配送费</span>
        </el-form-item>
        <el-form-item label="配送费">
          <el-input-number v-model="form.fee" :min="0" :precision="2" />
        </el-form-item>
        <el-form-item label="当前规则">
          <span class="preview">{{ preview }}</span>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="save">保存</el-button>
          <el-button @click="load">重置</el-button>
        </el-form-item>
      </el-form>
      <p class="muted tip">改动即时对新提交、新修改的订单生效，历史订单金额按下单时快照保留。</p>
    </el-card>
  </div>
</template>

<style scoped>
.card {
  max-width: 560px;
}

.hint,
.tip {
  margin-left: 8px;
  color: #909399;
  font-size: 12px;
}

.tip {
  margin: 0;
}

.preview {
  font-weight: 700;
  color: #f20d2f;
}
</style>
