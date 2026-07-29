const ALL_TABS = [
  {
    pagePath: '/pages/index/index',
    text: '首页',
    iconPath: '/static/tabbar/home.png',
    selectedIconPath: '/static/tabbar/home-active.png',
  },
  {
    pagePath: '/pages/category/index',
    text: '分类',
    iconPath: '/static/tabbar/category.png',
    selectedIconPath: '/static/tabbar/category-active.png',
  },
  {
    pagePath: '/pages/frequent/index',
    text: '常购清单',
    iconPath: '/static/tabbar/frequent.png',
    selectedIconPath: '/static/tabbar/frequent-active.png',
  },
  {
    pagePath: '/pages/cart/index',
    text: '购物车',
    iconPath: '/static/tabbar/cart.png',
    selectedIconPath: '/static/tabbar/cart-active.png',
  },
  {
    pagePath: '/pages/mine/index',
    text: '个人中心',
    iconPath: '/static/tabbar/user.png',
    selectedIconPath: '/static/tabbar/user-active.png',
  },
]

const GUEST_TABS = ALL_TABS.filter((_, index) => index !== 2)

Component({
  data: {
    selected: 0,
    tabList: GUEST_TABS,
  },

  lifetimes: {
    attached() {
      this.refresh()
    },
  },

  pageLifetimes: {
    show() {
      this.refresh()
    },
  },

  methods: {
    refresh() {
      const tabList = wx.getStorageSync('customer_token') ? ALL_TABS : GUEST_TABS
      const pages = getCurrentPages()
      const currentPage = pages[pages.length - 1]
      const currentPath = currentPage ? `/${currentPage.route}` : ''
      const selected = tabList.findIndex((item) => item.pagePath === currentPath)

      this.setData({
        tabList,
        selected: selected === -1 ? 0 : selected,
      })
    },

    switchTab(event) {
      const { path } = event.currentTarget.dataset
      if (!path) return
      wx.switchTab({ url: path })
    },
  },
})
