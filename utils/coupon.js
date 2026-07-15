// 优惠券金额计算：口径与后端 backend/app/services/coupon.py 的 compute_discount 保持一致。
// 前端仅做预估展示，最终以下单时服务端计算为准。

// 商品补送券：无金额/门槛，可叠加多张，仅作配货标记，不参与抵扣计算
export function isReissueCoupon(coupon) {
  return coupon?.kind === 'reissue'
}

export function couponDiscount(coupon, goodsTotal) {
  // 补送券不抵扣金额
  if (!coupon || isReissueCoupon(coupon)) return 0
  const total = Number(goodsTotal || 0)
  const minSpend = Number(coupon.min_spend || 0)
  if (total < minSpend) return 0
  return Math.min(Number(coupon.amount || 0), total)
}

// 券是否满足当前订单金额的使用门槛（仅针对满减券；补送券恒不作抵扣券）
export function isCouponUsable(coupon, goodsTotal) {
  if (!coupon || isReissueCoupon(coupon)) return false
  return Number(goodsTotal || 0) >= Number(coupon.min_spend || 0)
}

// 从满减券列表中挑出可用且抵扣最大的一张（补送券被 isCouponUsable 过滤掉）
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
