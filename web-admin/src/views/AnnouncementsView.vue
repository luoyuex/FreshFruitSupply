<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createAnnouncement, deleteAnnouncement, listAnnouncements, updateAnnouncement } from '../api'
import { dateTimeSec } from '../utils/format'

const loading = ref(false)
const rows = ref([])
const dialog = ref(false)
const saving = ref(false)
const form = reactive({ id: null, title: '', content: '', is_active: true })

async function load() {
  loading.value = true
  try {
    rows.value = await listAnnouncements()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

function open(row) {
  Object.assign(form, row ? { ...row } : { id: null, title: '', content: '', is_active: true })
  dialog.value = true
}

async function save() {
  if (!form.title.trim() || !form.content.trim()) {
    ElMessage.warning('标题和内容都要填写')
    return
  }
  const payload = { title: form.title.trim(), content: form.content, is_active: !!form.is_active }
  saving.value = true
  try {
    if (form.id) await updateAnnouncement(form.id, payload)
    else await createAnnouncement(payload)
    ElMessage.success('已保存')
    dialog.value = false
    await load()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    saving.value = false
  }
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(`确认删除公告「${row.title}」？删除后不可恢复。`, '删除公告', { type: 'warning' })
  } catch (error) {
    return
  }
  try {
    await deleteAnnouncement(row.id)
    ElMessage.success('已删除')
    await load()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-toolbar">
      <span class="muted">启用中的公告会出现在小程序公告页。</span>
      <div class="grow"></div>
      <el-button @click="load">刷新</el-button>
      <el-button type="primary" @click="open(null)">新增公告</el-button>
    </div>

    <el-table v-loading="loading" :data="rows" border>
      <el-table-column label="标题" min-width="180" prop="title" />
      <el-table-column label="内容" min-width="320">
        <template #default="{ row }"><pre class="content">{{ row.content }}</pre></template>
      </el-table-column>
      <el-table-column label="状态" width="110">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '展示给用户' : '已隐藏' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="180">
        <template #default="{ row }">{{ dateTimeSec(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="open(row)">编辑</el-button>
          <el-button size="small" type="danger" plain @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
      <template #empty><span class="muted">还没有公告</span></template>
    </el-table>

    <el-dialog v-model="dialog" :title="form.id ? '编辑公告' : '新增公告'" width="560px">
      <el-form label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" maxlength="60" show-word-limit />
        </el-form-item>
        <el-form-item label="内容" required>
          <el-input v-model="form.content" type="textarea" :rows="6" placeholder="支持换行" />
        </el-form-item>
        <el-form-item label="展示">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.content {
  margin: 0;
  font-family: inherit;
  white-space: pre-wrap;
}
</style>
