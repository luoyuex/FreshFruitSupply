const CART_KEY = 'fruit_quote_cart'

function readCart() {
  try {
    return JSON.parse(uni.getStorageSync(CART_KEY) || '[]')
  } catch (error) {
    return []
  }
}

function writeCart(items) {
  uni.setStorageSync(CART_KEY, JSON.stringify(items))
  return items
}

export function getCartItems() {
  return readCart()
}

export function addCartItem(fruit, quantity = 1) {
  const items = readCart()
  const existing = items.find((item) => item.id === fruit.id)
  if (existing) {
    existing.quantity = Number(existing.quantity || 0) + Number(quantity || 1)
  } else {
    items.push({
      id: fruit.id,
      name: fruit.name,
      category: fruit.category,
      origin: fruit.origin,
      image_url: fruit.image_url || fruit.image_urls?.[0] || '',
      image_urls: fruit.image_urls || (fruit.image_url ? [fruit.image_url] : []),
      spec: fruit.spec,
      unit: fruit.unit,
      stock_status: fruit.stock_status,
      normal_price: fruit.quote?.normal_price || 0,
      verified_price: fruit.quote?.verified_price || 0,
      min_order_quantity: Number(fruit.quote?.min_order_quantity || 1),
      quantity: Number(quantity || fruit.quote?.min_order_quantity || 1),
      selected: true,
    })
  }
  return writeCart(items)
}

export function updateCartItem(id, patch) {
  const items = readCart().map((item) => (item.id === id ? { ...item, ...patch } : item))
  return writeCart(items)
}

export function removeCartItem(id) {
  return writeCart(readCart().filter((item) => item.id !== id))
}

export function clearSelectedCartItems(ids) {
  const idSet = new Set(ids)
  return writeCart(readCart().filter((item) => !idSet.has(item.id)))
}

export function cartCount() {
  return readCart().reduce((sum, item) => sum + Number(item.quantity || 0), 0)
}
