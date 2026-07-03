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
</style>
