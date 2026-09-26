<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { ElMessageBox } from 'element-plus'
import { roleLabel } from '../utils/format'

const route = useRoute()
const router = useRouter()
const store = useStore()

const navItems = computed(() => store.getters.navItems)
const admin = computed(() => store.state.admin)

async function onCommand(command) {
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
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
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
