<script setup>
import { computed, onMounted, reactive, shallowRef } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { request } from '../../../utils/request.js'
import { shortDateTime } from '../../../utils/format.js'
import { goAdminNav, redirectIfNoPermission, visibleAdminNavItems } from '../../../utils/admin.js'

const announcements = shallowRef([])
const loading = shallowRef(false)
const saving = shallowRef(false)
const removing = shallowRef(false)
const modalVisible = shallowRef(false)
const editingId = shallowRef(null)
const navItems = computed(() => visibleAdminNavItems())

const form = reactive({
  title: '',
  content: '',
  isActive: true,
})

async function loadList() {
  loading.value = true
  try {
    announcements.value = await request({ url: '/admin/announcements', admin: true })
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  form.title = ''
  form.content = ''
  form.isActive = true
  modalVisible.value = true
}

function openEdit(item) {
  editingId.value = item.id
  form.title = item.title
  form.content = item.content
  form.isActive = item.is_active
  modalVisible.value = true
}

function closeModal() {
  modalVisible.value = false
}

function validate() {
  if (!form.title.trim()) return '请填写公告标题'
  if (!form.content.trim()) return '请填写公告内容'
  return ''
}

async function save() {
  const message = validate()
  if (message) {
    uni.showToast({ title: message, icon: 'none' })
    return
  }
  saving.value = true
  const payload = {
    title: form.title.trim(),
    content: form.content.trim(),
    is_active: form.isActive,
  }
  try {
    if (editingId.value) {
      await request({ url: `/admin/announcements/${editingId.value}`, method: 'PATCH', admin: true, data: payload })
    } else {
      await request({ url: '/admin/announcements', method: 'POST', admin: true, data: payload })
    }
    modalVisible.value = false
    await loadList()
    uni.showToast({ title: '已保存', icon: 'success' })
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
  } finally {
    saving.value = false
  }
}

function remove() {
  if (!editingId.value) return
  uni.showModal({
    title: '删除公告',
    content: '删除后用户将不再看到这条公告，确认删除？',
    success: async (res) => {
      if (!res.confirm) return
      removing.value = true
      try {
        await request({ url: `/admin/announcements/${editingId.value}`, method: 'DELETE', admin: true })
        modalVisible.value = false
        await loadList()
        uni.showToast({ title: '已删除', icon: 'success' })
      } catch (err) {
        uni.showToast({ title: err.message, icon: 'none' })
      } finally {
        removing.value = false
      }
    },
  })
}

function guardedLoad() {
  if (redirectIfNoPermission('settings')) return
  loadList()
}

onMounted(guardedLoad)
onShow(guardedLoad)

onPullDownRefresh(async () => {
  try {
    await loadList()
  } finally {
    uni.stopPullDownRefresh()
  }
})
</script>

<template>
  <view class="page">
    <view class="admin-nav">
      <button v-for="item in navItems" :key="item.key" class="nav-button" :class="{ active: item.key === 'settings' }" @tap="goAdminNav(item)">{{ item.label }}</button>
    </view>

    <view class="top-actions">
      <button class="create-btn" @tap="openCreate">+ 新建公告</button>
    </view>

    <view v-if="loading && !announcements.length" class="empty">正在加载公告...</view>
    <view v-else-if="!announcements.length" class="empty">还没有公告，点击上方新建</view>

    <view v-for="item in announcements" :key="item.id" class="card" @tap="openEdit(item)">
      <view class="card-head">
        <text class="tpl-title">{{ item.title }}</text>
        <text class="tpl-state" :class="{ off: !item.is_active }">{{ item.is_active ? '展示中' : '已隐藏' }}</text>
      </view>
      <view class="tpl-content">{{ item.content }}</view>
      <view class="tpl-meta">{{ shortDateTime(item.created_at) }}</view>
    </view>

    <view v-if="modalVisible" class="modal-mask" @tap="closeModal">
      <view class="modal-card" @tap.stop>
        <view class="modal-title">{{ editingId ? '编辑公告' : '新建公告' }}</view>
        <view class="field">
          <text class="label">标题</text>
          <input v-model="form.title" class="input" placeholder="如 春节配送安排" />
        </view>
        <view class="field">
          <text class="label">内容</text>
          <textarea v-model="form.content" class="textarea" placeholder="公告正文，支持换行" />
        </view>
        <view class="switch-row">
          <text class="label">展示给用户</text>
          <switch :checked="form.isActive" color="#2f6b23" @change="form.isActive = $event.detail.value" />
        </view>
        <view class="modal-actions">
          <button v-if="editingId" class="delete" :loading="removing" :disabled="removing" @tap="remove">删除</button>
          <button class="cancel" @tap="closeModal">取消</button>
          <button class="save" :loading="saving" :disabled="saving" @tap="save">保存</button>
        </view>
      </view>
    </view>
  </view>
</template>

<style scoped>
.page { min-height: 100vh; padding: 24rpx; background: #f5f8ef; box-sizing: border-box; }
.admin-nav { display: flex; flex-wrap: wrap; gap: 10rpx; margin-bottom: 20rpx; }
.nav-button { flex: 1; min-width: 120rpx; height: 70rpx; line-height: 70rpx; padding: 0; border-radius: 999rpx; color: #2f4b21; background: #fff; font-size: 23rpx; }
.nav-button.active { color: #fff; background: #2f6b23; }
.nav-button::after { border: none; }

.top-actions { display: flex; }
.create-btn {
  flex: 1;
  height: 84rpx;
  line-height: 84rpx;
  border-radius: 18rpx;
  color: #fff;
  background: #2f6b23;
  font-size: 28rpx;
  font-weight: 800;
}
.create-btn::after { border: none; }

.card, .empty { margin-top: 18rpx; padding: 24rpx; border-radius: 26rpx; background: #fff; box-shadow: 0 10rpx 26rpx rgba(73,83,47,.08); }
.empty { text-align: center; color: #7a8a72; font-size: 26rpx; }

.card-head { display: flex; align-items: center; justify-content: space-between; gap: 16rpx; }
.tpl-title { flex: 1; min-width: 0; color: #173b16; font-size: 30rpx; font-weight: 900; }
.tpl-state { flex-shrink: 0; color: #2f6b23; font-size: 23rpx; font-weight: 800; }
.tpl-state.off { color: #999; }
.tpl-content { margin-top: 14rpx; color: #4a5646; font-size: 26rpx; line-height: 1.6; }
.tpl-meta { margin-top: 12rpx; color: #9aa792; font-size: 23rpx; }

.modal-mask {
  position: fixed;
  z-index: 90;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40rpx;
  background: rgba(0, 0, 0, .45);
  box-sizing: border-box;
}

.modal-card {
  width: 100%;
  max-height: 84vh;
  overflow-y: auto;
  padding: 34rpx 30rpx;
  border-radius: 28rpx;
  background: #fff;
  box-sizing: border-box;
}

.modal-title { color: #173b16; font-size: 34rpx; font-weight: 900; text-align: center; }

.field { margin-top: 22rpx; }
.label { color: #445; font-size: 25rpx; }
.input {
  width: 100%;
  height: 78rpx;
  margin-top: 12rpx;
  padding: 0 22rpx;
  border-radius: 16rpx;
  color: #222;
  background: #f4f6f0;
  box-sizing: border-box;
  font-size: 27rpx;
}
.textarea {
  width: 100%;
  height: 240rpx;
  margin-top: 12rpx;
  padding: 18rpx 22rpx;
  border-radius: 16rpx;
  color: #222;
  background: #f4f6f0;
  box-sizing: border-box;
  font-size: 27rpx;
  line-height: 1.6;
}

.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 24rpx;
}

.modal-actions { display: flex; gap: 16rpx; margin-top: 34rpx; }
.cancel, .save, .delete { flex: 1; height: 82rpx; line-height: 82rpx; border-radius: 16rpx; font-size: 28rpx; font-weight: 800; }
.cancel { color: #555; background: #eef0ea; }
.save { color: #fff; background: #2f6b23; }
.delete { color: #fff; background: #ef4444; }
.cancel::after, .save::after, .delete::after { border: none; }
</style>
