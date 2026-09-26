import { loadEnv, defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const target = env.VITE_PROXY_TARGET || 'https://zhenguolian.cn'
  return {
    plugins: [vue()],
    server: {
      host: '0.0.0.0',
      port: Number(env.VITE_PORT || 5180),
      proxy: {
        '/api': { target, changeOrigin: true },
        '/uploads': { target, changeOrigin: true },
      },
    },
  }
})
