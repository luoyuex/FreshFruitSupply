export const CATEGORY_ICON_ITEMS = [
  { id: 'noto:red-apple', label: '红苹果', path: '/static/icons/fruits/noto-red-apple.svg', recommended: true },
  { id: 'noto:banana', label: '香蕉', path: '/static/icons/fruits/noto-banana.svg', recommended: true },
  { id: 'noto:tangerine', label: '橙子/柑橘', path: '/static/icons/fruits/noto-tangerine.svg', recommended: true },
  { id: 'noto:grapes', label: '葡萄', path: '/static/icons/fruits/noto-grapes.svg', recommended: true },
  { id: 'noto:pear', label: '梨', path: '/static/icons/fruits/noto-pear.svg', recommended: true },
  { id: 'noto:peach', label: '桃', path: '/static/icons/fruits/noto-peach.svg', recommended: true },
  { id: 'noto:strawberry', label: '草莓', path: '/static/icons/fruits/noto-strawberry.svg', recommended: true },
  { id: 'noto:watermelon', label: '西瓜', path: '/static/icons/fruits/noto-watermelon.svg', recommended: true },
  { id: 'noto:mango', label: '芒果', path: '/static/icons/fruits/noto-mango.svg', recommended: true },
  { id: 'noto:pineapple', label: '菠萝', path: '/static/icons/fruits/noto-pineapple.svg', recommended: true },
  { id: 'noto:lemon', label: '柠檬', path: '/static/icons/fruits/noto-lemon.svg', recommended: true },
  { id: 'noto:cherries', label: '樱桃/车厘子', path: '/static/icons/fruits/noto-cherries.svg', recommended: true },
  { id: 'noto:green-apple', label: '青苹果', path: '/static/icons/fruits/noto-green-apple.svg', recommended: false },
  { id: 'noto:kiwi-fruit', label: '猕猴桃/奇异果', path: '/static/icons/fruits/noto-kiwi-fruit.svg', recommended: false },
  { id: 'noto:coconut', label: '椰子', path: '/static/icons/fruits/noto-coconut.svg', recommended: false },
  { id: 'noto:blueberries', label: '蓝莓', path: '/static/icons/fruits/noto-blueberries.svg', recommended: false },
  { id: 'noto:melon', label: '哈密瓜/甜瓜', path: '/static/icons/fruits/noto-melon.svg', recommended: false },
  { id: 'noto:avocado', label: '牛油果', path: '/static/icons/fruits/noto-avocado.svg', recommended: false },
  { id: 'noto:tomato', label: '番茄', path: '/static/icons/fruits/noto-tomato.svg', recommended: false },
  { id: 'noto:olive', label: '橄榄', path: '/static/icons/fruits/noto-olive.svg', recommended: false },
  { id: 'noto:bell-pepper', label: '彩椒', path: '/static/icons/fruits/noto-bell-pepper.svg', recommended: false },
  { id: 'noto:cucumber', label: '黄瓜', path: '/static/icons/fruits/noto-cucumber.svg', recommended: false },
  { id: 'noto:hot-pepper', label: '辣椒', path: '/static/icons/fruits/noto-hot-pepper.svg', recommended: false },
]

const CATEGORY_ICON_MAP = CATEGORY_ICON_ITEMS.reduce((map, item) => {
  map[item.id] = item
  return map
}, {})

export function categoryIconPath(icon) {
  // 如果传入的是对象，优先使用 icon_url
  if (icon && typeof icon === 'object') {
    if (icon.icon_url) {
      return icon.icon_url
    }
    return CATEGORY_ICON_MAP[icon.icon]?.path || ''
  }
  // 否则当做字符串处理
  return CATEGORY_ICON_MAP[icon]?.path || ''
}

export function categoryIconLabel(icon) {
  return CATEGORY_ICON_MAP[icon]?.label || ''
}

export function isCategoryIconRecommended(icon) {
  return Boolean(CATEGORY_ICON_MAP[icon]?.recommended)
}
