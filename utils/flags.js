import { reactive } from 'vue'
import { request } from './request.js'

// C 端功能开关：App 启动时从后端 /config/client 拉取一次并缓存本地。
// 后端切换开关后无需前端发版——用户下次冷启动小程序即生效。
// 拉取失败沿用本地缓存；从未拉到过时默认全关（隐藏入口，符合快速上线期的保守姿态）。

const STORAGE_KEY = 'client_flags'

export const flags = reactive(uni.getStorageSync(STORAGE_KEY) || { verification_enabled: false })

export async function loadClientFlags() {
  try {
    const data = await request({ url: '/config/client' })
    flags.verification_enabled = !!data.verification_enabled
    uni.setStorageSync(STORAGE_KEY, { verification_enabled: flags.verification_enabled })
  } catch (err) {
    // 网络异常时沿用本地缓存，不阻塞启动
  }
}
