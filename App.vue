<script setup>
import { onHide, onLaunch, onShow } from '@dcloudio/uni-app'

onLaunch(() => {
  console.log('Fruit quote app launch')
})

onShow(() => {
  console.log('Fruit quote app show')
})

onHide(() => {
  console.log('Fruit quote app hide')
})
</script>

<style>
page {
  color: #222222;
  background: #f3f3f3;
  font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
}

button {
  padding: 0;
  margin: 0;
  border: 0;
  background: transparent;
}

button::after {
  border: 0;
}

input,
textarea {
  caret-color: #ffb700;
}

/* 骨架屏通用样式 */
.skeleton {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
