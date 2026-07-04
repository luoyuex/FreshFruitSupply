// 临时验证脚本：复制 pages/address/index.vue 里的 parseRegion 实现
function parseRegion(address = '') {
  const text = String(address || '')
  const municipalities = ['北京市', '上海市', '天津市', '重庆市']
  let province = ''
  let city = ''
  let district = ''
  let rest = text
  const prov = text.match(/^(.+?(?:省|特别行政区|自治区))/)
  if (prov) {
    province = prov[1]
    rest = text.slice(province.length)
  } else {
    const muni = municipalities.find((x) => text.startsWith(x))
    if (muni) {
      province = muni
      rest = text.slice(muni.length)
    }
  }
  const cm = rest.match(/^(.+?(?:市|自治州|地区|盟))/)
  if (cm) {
    city = cm[1]
    rest = rest.slice(city.length)
  } else if (municipalities.includes(province)) {
    city = province
  }
  const dm = rest.match(/^(.+?(?:区|县|旗))/)
  if (dm) {
    district = dm[1]
    rest = rest.slice(district.length)
  }
  return { province, city, district, detail: rest.trim() }
}

const cases = [
  { in: '广东省广州市天河区五山路1号', p: '广东省', c: '广州市', d: '天河区', detail: '五山路1号' },
  { in: '北京市海淀区中关村大街1号', p: '北京市', c: '北京市', d: '海淀区', detail: '中关村大街1号' },
  { in: '上海市浦东新区世纪大道100号', p: '上海市', c: '上海市', d: '浦东新区', detail: '世纪大道100号' },
  { in: '新疆维吾尔自治区乌鲁木齐市天山区人民路1号', p: '新疆维吾尔自治区', c: '乌鲁木齐市', d: '天山区', detail: '人民路1号' },
  { in: '内蒙古自治区呼伦贝尔市鄂温克族自治旗巴彦托海镇', p: '内蒙古自治区', c: '呼伦贝尔市', d: '鄂温克族自治旗', detail: '巴彦托海镇' },
  { in: '浙江省金华市义乌市稠城街道1号', p: '浙江省', c: '金华市', d: '', detail: '义乌市稠城街道1号' }, // 县级市：district 拆不出，留在 detail（无信息丢失）
  { in: '', p: '', c: '', d: '', detail: '' }, // 空串兜底
]

let pass = 0
let fail = 0
for (const t of cases) {
  const r = parseRegion(t.in)
  // 无信息丢失校验：province+city(直辖市重复只算一次)+district+detail 应能覆盖原串关键片段
  const joined = r.province + (r.city === r.province ? '' : r.city) + r.district + r.detail
  const ok = r.province === t.p && r.city === t.c && r.district === t.d && r.detail === t.detail
  const lossless = t.in === '' || joined.replace(/\s/g, '') === t.in.replace(/\s/g, '')
  if (ok && lossless) {
    pass++
    console.log('PASS  ', JSON.stringify(t.in))
  } else {
    fail++
    console.log('FAIL  ', JSON.stringify(t.in))
    console.log('   期望', JSON.stringify({ p: t.p, c: t.c, d: t.d, detail: t.detail }))
    console.log('   实得', JSON.stringify(r))
    if (!lossless) console.log('   ⚠ 信息丢失: joined=', JSON.stringify(joined))
  }
}
console.log(`\n结果: ${pass} 通过, ${fail} 失败`)
process.exit(fail ? 1 : 0)
