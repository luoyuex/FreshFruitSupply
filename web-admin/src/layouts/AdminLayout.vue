<script setup>
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { ElMessage, ElMessageBox } from 'element-plus'
import { changeMyPassword } from '../api'
import { roleLabel } from '../utils/format'

const route = useRoute()
const router = useRouter()
const store = useStore()

const navItems = computed(() => store.getters.navItems)
const admin = computed(() => store.state.admin)

const passwordDialog = ref(false)
const changing = ref(false)
const passwordForm = reactive({ old_password: '', new_password: '', confirm: '' })

function openPasswordDialog() {
  passwordForm.old_password = ''
  passwordForm.new_password = ''
  passwordForm.confirm = ''
  passwordDialog.value = true
}

async function submitPassword() {
  if (passwordForm.new_password.length < 6) {
    ElMessage.warning('新密码至少 6 位')
    return
  }
  if (passwordForm.new_password !== passwordForm.confirm) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  changing.value = true
  try {
    await changeMyPassword({ old_password: passwordForm.old_password, new_password: passwordForm.new_password })
    passwordDialog.value = false
    // 令牌未失效，无需重新登录；旧密码此刻已作废
    ElMessage.success('密码已修改')
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    changing.value = false
  }
}

async function onCommand(command) {
  if (command === 'password') {
    openPasswordDialog()
    return
  }
  if (command !== 'logout') return
  await ElMessageBox.confirm('确认退出登录？', '提示', { type: 'warning' })
  store.dispatch('logout')
  router.replace('/login')
}
</script>

<template>
  <el-container class="shell">
    <el-aside width="200px" class="aside">
      <div class="brand">鲜果供应后台</div>
      <el-menu :default-active="route.path" router class="menu">
        <el-menu-item v-for="item in navItems" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="title">{{ route.meta.title }}</div>
        <el-dropdown @command="onCommand">
          <span class="account">
            {{ admin?.nickname || admin?.username || '管理员' }}
            <el-tag size="small" type="warning">{{ roleLabel(admin?.role) }}</el-tag>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="password">修改密码</el-dropdown-item>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
    <el-dialog v-model="passwordDialog" title="修改密码" width="420px">
      <el-form label-width="96px">
        <el-form-item label="原密码">
          <el-input v-model="passwordForm.old_password" type="password" show-password autocomplete="current-password" />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="passwordForm.new_password" type="password" show-password placeholder="至少 6 位" autocomplete="new-password" />
        </el-form-item>
        <el-form-item label="确认新密码">
          <el-input v-model="passwordForm.confirm" type="password" show-password autocomplete="new-password" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialog = false">取消</el-button>
        <el-button type="primary" :loading="changing" @click="submitPassword">保存</el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<style scoped>
.shell {
  height: 100%;
}

.aside {
  background: #1f2d3d;
  overflow-x: hidden;
}

.brand {
  height: 56px;
  line-height: 56px;
  padding-left: 20px;
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  background: #17212e;
}

.menu {
  border-right: none;
  background: #1f2d3d;
}

.menu :deep(.el-menu-item) {
  color: #c5ccd6;
}

.menu :deep(.el-menu-item.is-active) {
  color: #fff;
  background: #2f4b6e;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}

.title {
  font-size: 16px;
  font-weight: 700;
}

.account {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  outline: none;
}

.main {
  padding: 0;
  overflow-y: auto;
}
</style>
