<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const store = useStore()

const form = reactive({ username: '', password: '' })
const submitting = ref(false)

async function submit() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  submitting.value = true
  try {
    await store.dispatch('login', { ...form })
    ElMessage.success('登录成功')
    router.replace(route.query.redirect || '/orders')
  } catch (error) {
    ElMessage.error(error.message || '登录失败')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <el-card class="login-card">
      <div class="login-title">鲜果供应 · 后台管理</div>
      <el-form label-position="top" @submit.prevent="submit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="请输入管理员用户名" clearable @keyup.enter="submit" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password @keyup.enter="submit" />
        </el-form-item>
        <el-button type="primary" class="submit" :loading="submitting" @click="submit">登录</el-button>
      </el-form>
      <p class="tip">账号与小程序后台通用，权限由管理员角色决定。</p>
    </el-card>
  </div>
</template>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: linear-gradient(135deg, #1f2d3d, #2f4b6e);
}

.login-card {
  width: 380px;
  padding: 8px 12px 16px;
}

.login-title {
  margin-bottom: 18px;
  font-size: 19px;
  font-weight: 800;
  text-align: center;
}

.submit {
  width: 100%;
}

.tip {
  margin: 16px 0 0;
  color: #909399;
  font-size: 12px;
  text-align: center;
}
</style>
