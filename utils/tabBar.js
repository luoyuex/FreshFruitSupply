export function refreshCustomTabBar() {
  // #ifdef MP-WEIXIN
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  if (!currentPage || typeof currentPage.getTabBar !== 'function') return

  const tabBar = currentPage.getTabBar()
  if (tabBar && typeof tabBar.refresh === 'function') {
    tabBar.refresh()
  }
  // #endif
}
