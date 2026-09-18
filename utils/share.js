export function getShareOptions(shareConfig = {}) {
  const defaultConfig = {
    title: '珍果链 - 新鲜水果次日达',
    path: '/pages/index/index',
    imageUrl: '',
    query: ''
  }
  
  return { ...defaultConfig, ...shareConfig }
}

export function getShareAppMessage(shareConfig = {}) {
  const config = getShareOptions(shareConfig)
  return {
    title: config.title,
    path: config.path,
    imageUrl: config.imageUrl
  }
}

export function getShareTimeline(shareConfig = {}) {
  const config = getShareOptions(shareConfig)
  return {
    title: config.title,
    query: config.query,
    imageUrl: config.imageUrl
  }
}
