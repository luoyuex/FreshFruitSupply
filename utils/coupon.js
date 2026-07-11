// 优惠券金额计算：口径与后端 backend/app/services/coupon.py 的 compute_discount 保持一致。
// 前端仅做预估展示，最终以下单时服务端计算为准。

export function couponDiscount(coupon, goodsTotal) {
  if (!coupon) return 0
  const total = Number(goodsTotal || 0)
  const minSpend = Number(coupon.min_spend || 0)
  if (total < minSpend) return 0
  return Math.min(Number(coupon.amount || 0), total)
}

// 券是否满足当前订单金额的使用门槛
export function isCouponUsable(coupon, goodsTotal) {
  if (!coupon) return false
  return Number(goodsTotal || 0) >= Number(coupon.min_spend || 0)
}

// 从券列表中挑出可用且抵扣最大的一张
export function pickBestCoupon(coupons, goodsTotal) {
  let best = null
  let bestDiscount = 0
  for (const coupon of coupons || []) {
    if (!isCouponUsable(coupon, goodsTotal)) continue
    const discount = couponDiscount(coupon, goodsTotal)
    if (discount > bestDiscount) {
      best = coupon
      bestDiscount = discount
    }
  }
  return best
}
