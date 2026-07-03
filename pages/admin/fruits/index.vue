<script setup>
import { computed, onMounted, reactive, shallowRef } from 'vue'
import { onPullDownRefresh } from '@dcloudio/uni-app'
import { request, uploadAdminImage } from '../../../utils/request.js'
import { money, statusLabel } from '../../../utils/format.js'
import { goAdminNav, redirectIfNoPermission, visibleAdminNavItems } from '../../../utils/admin.js'
import { CATEGORY_ICON_ITEMS, categoryIconLabel, categoryIconPath } from '../../../utils/categoryIcons.js'

const fruits = shallowRef([])
const categories = shallowRef([])
const loading = shallowRef(false)
const saving = shallowRef(false)
const activeCategoryId = shallowRef('all')
const keyword = shallowRef('')
const fruitModalVisible = shallowRef(false)
const categoryModalVisible = shallowRef(false)
const iconPickerVisible = shallowRef(false)
const editingFruitId = shallowRef(null)
const editingCategoryId = shallowRef(null)

const stockValues = ['in_stock', 'limited', 'out_of_stock']
const maxDetailImages = 18
const form = reactive({
  name: '',
  category_id: '',
  origin: '',
  spec: '',
  unit: '斤',
  stock_status: 'in_stock',
  is_recommended: false,
  normal_price: '',
  verified_price: '',
  grade: '一级',
  min_order_quantity: 1,
  note: '',
  image_url: '',
  detail_image_urls: [],
})
const categoryForm = reactive({ name: '', icon: '', icon_url: '', sort_order: 0, is_active: true })

const navItems = computed(() => visibleAdminNavItems())
const categoryNames = computed(() => categories.value.map((item) => `${item.name}${item.is_active ? '' : '（停用）'}`))
const selectedCategoryName = computed(() => categories.value.find((item) => item.id === Number(form.category_id))?.name || '请选择分类')
const categoryPickerIndex = computed(() => Math.max(0, categories.value.findIndex((item) => item.id === Number(form.category_id))))
const recommendedCategoryIcons = computed(() => CATEGORY_ICON_ITEMS.filter((item) => item.recommended))
const allCategoryIcons = computed(() => CATEGORY_ICON_ITEMS)
const selectedCategoryIconPath = computed(() => categoryIconPath(categoryForm.icon))
const selectedCategoryIconLabel = computed(() => categoryIconLabel(categoryForm.icon))
const stockPickerIndex = computed(() => Math.max(0, stockValues.indexOf(form.stock_status)))
const filteredFruits = computed(() => {
  const text = keyword.value.trim()
  return fruits.value.filter((fruit) => {
    const matchesCategory = activeCategoryId.value === 'all' || Number(fruit.category_id) === Number(activeCategoryId.value)
    const matchesKeyword = !text || fruit.name.includes(text) || fruit.origin?.includes(text) || fruit.spec?.includes(text)
    return matchesCategory && matchesKeyword
  })
})

async function loadCategories() {
  categories.value = await request({ url: '/admin/categories', admin: true })
}

async function loadFruits() {
  fruits.value = await request({ url: '/fruits' })
}

async function loadAll() {
  loading.value = true
  try {
    await Promise.all([loadCategories(), loadFruits()])
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
    if (err.message.includes('token') || err.message.includes('Missing')) {
      uni.redirectTo({ url: '/pages/admin/login/index' })
    }
  } finally {
    loading.value = false
  }
}

function resetFruitForm() {
  editingFruitId.value = null
  Object.assign(form, {
    name: '',
    category_id: activeCategoryId.value !== 'all' && activeCategoryId.value !== 'category_manager' ? activeCategoryId.value : (categories.value[0]?.id || ''),
    origin: '',
    spec: '',
    unit: '斤',
    stock_status: 'in_stock',
    is_recommended: false,
    normal_price: '',
    verified_price: '',
    grade: '一级',
    min_order_quantity: 1,
    note: '',
    image_url: '',
    detail_image_urls: [],
  })
}

function openFruitModal(fruit = null) {
  if (!categories.value.length) {
    uni.showToast({ title: '请先新增分类', icon: 'none' })
    return
  }
  resetFruitForm()
  if (fruit) {
    editingFruitId.value = fruit.id
    Object.assign(form, {
      name: fruit.name,
      category_id: fruit.category_id || categories.value.find((item) => item.name === fruit.category)?.id || categories.value[0]?.id || '',
      origin: fruit.origin || '',
      spec: fruit.spec,
      unit: fruit.unit,
      stock_status: fruit.stock_status,
      is_recommended: fruit.is_recommended,
      normal_price: fruit.quote?.normal_price || '',
      verified_price: fruit.quote?.verified_price || '',
      grade: fruit.quote?.grade || '一级',
      min_order_quantity: fruit.quote?.min_order_quantity || 1,
      note: fruit.quote?.note || '',
      image_url: fruit.image_url || fruit.image_urls?.[0] || '',
      detail_image_urls: fruit.detail_image_urls?.length ? fruit.detail_image_urls : (fruit.image_urls || []).slice(1),
    })
  }
  fruitModalVisible.value = true
}

function closeFruitModal() {
  fruitModalVisible.value = false
  resetFruitForm()
}

function changeFruitCategory(event) {
  form.category_id = categories.value[event.detail.value]?.id || ''
}

function changeStock(event) {
  form.stock_status = stockValues[event.detail.value] || 'in_stock'
}

async function uploadImageFiles(filePaths, onUploaded) {
  try {
    uni.showLoading({ title: '压缩上传中' })
    for (const filePath of filePaths) {
      const data = await uploadAdminImage(filePath)
      if (data.url) onUploaded(data.url)
    }
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
  } finally {
    uni.hideLoading()
  }
}

async function chooseCoverImage() {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      uploadImageFiles(res.tempFilePaths, (url) => {
        form.image_url = url
      })
    },
  })
}

async function chooseDetailImages() {
  if (form.detail_image_urls.length >= maxDetailImages) {
    uni.showToast({ title: `最多上传${maxDetailImages}张详情图`, icon: 'none' })
    return
  }
  uni.chooseImage({
    count: Math.max(1, maxDetailImages - form.detail_image_urls.length),
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      uploadImageFiles(res.tempFilePaths, (url) => {
        if (!form.detail_image_urls.includes(url)) form.detail_image_urls.push(url)
      })
    },
  })
}

function removeCoverImage() {
  form.image_url = ''
}

function removeDetailImage(index) {
  form.detail_image_urls.splice(index, 1)
}

function previewCoverImage() {
  if (!form.image_url) return
  uni.previewImage({ urls: [form.image_url], current: form.image_url })
}

function previewDetailImages(url) {
  uni.previewImage({ urls: form.detail_image_urls, current: url })
}

async function chooseCategoryIcon() {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      uploadImageFiles(res.tempFilePaths, (url) => {
        categoryForm.icon_url = url
        categoryForm.icon = ''
      })
    },
  })
}

function clearCategoryIconUrl() {
  categoryForm.icon_url = ''
}

function previewCategoryIcon() {
  if (!categoryForm.icon_url) return
  uni.previewImage({ urls: [categoryForm.icon_url], current: categoryForm.icon_url })
}

async function saveFruit() {
  if (!form.name || !form.category_id || !form.spec || !form.normal_price || !form.verified_price) {
    uni.showToast({ title: '请补全水果、分类、规格和价格', icon: 'none' })
    return
  }
  saving.value = true
  const url = editingFruitId.value ? `/admin/fruits/${editingFruitId.value}` : '/admin/fruits'
  const method = editingFruitId.value ? 'PATCH' : 'POST'
  try {
    await request({
      url,
      method,
      admin: true,
      data: {
        ...form,
        category_id: Number(form.category_id),
        image_url: form.image_url,
        image_urls: form.image_url ? [form.image_url] : [],
        normal_price: Number(form.normal_price),
        verified_price: Number(form.verified_price),
        min_order_quantity: Number(form.min_order_quantity),
      },
    })
    uni.showToast({ title: '已保存', icon: 'success' })
    closeFruitModal()
    await loadFruits()
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
  } finally {
    saving.value = false
  }
}

function openCategoryModal(category = null) {
  editingCategoryId.value = category?.id || null
  Object.assign(categoryForm, {
    name: category?.name || '',
    icon: category?.icon || '',
    icon_url: category?.icon_url || '',
    sort_order: category?.sort_order ?? ((categories.value.length + 1) * 10),
    is_active: category?.is_active ?? true,
  })
  categoryModalVisible.value = true
}

function closeCategoryModal() {
  categoryModalVisible.value = false
  iconPickerVisible.value = false
  editingCategoryId.value = null
  Object.assign(categoryForm, { name: '', icon: '', icon_url: '', sort_order: 0, is_active: true })
}

function openIconPicker() {
  iconPickerVisible.value = true
}

function closeIconPicker() {
  iconPickerVisible.value = false
}

function selectCategoryIcon(icon) {
  categoryForm.icon = icon.id
  closeIconPicker()
}

function clearCategoryIcon() {
  categoryForm.icon = ''
  closeIconPicker()
}

async function saveCategory() {
  if (!categoryForm.name.trim()) {
    uni.showToast({ title: '请填写分类名称', icon: 'none' })
    return
  }
  saving.value = true
  const url = editingCategoryId.value ? `/admin/categories/${editingCategoryId.value}` : '/admin/categories'
  const method = editingCategoryId.value ? 'PATCH' : 'POST'
  try {
    await request({
      url,
      method,
      admin: true,
      data: {
        name: categoryForm.name.trim(),
        icon: categoryForm.icon || null,
        icon_url: categoryForm.icon_url || null,
        sort_order: Number(categoryForm.sort_order || 0),
        is_active: Boolean(categoryForm.is_active),
      },
    })
    uni.showToast({ title: '分类已保存', icon: 'success' })
    closeCategoryModal()
    await Promise.all([loadCategories(), loadFruits()])
  } catch (err) {
    uni.showToast({ title: err.message, icon: 'none' })
  } finally {
    saving.value = false
  }
}

function setActiveCategory(id) {
  activeCategoryId.value = id
}

onMounted(() => {
  if (redirectIfNoPermission('fruits')) return
  loadAll()
})

onPullDownRefresh(async () => {
  try {
    await loadAll()
  } finally {
    uni.stopPullDownRefresh()
  }
})
</script>

<template>
  <view class="page">
    <view class="admin-nav">
      <button v-for="item in navItems" :key="item.key" class="nav-button" :class="{ active: item.key === 'fruits' }" @tap="goAdminNav(item)">{{ item.label }}</button>
    </view>

    <view class="toolbar">
      <input v-model="keyword" class="search" placeholder="搜索水果、产地、规格" />
      <button class="toolbar-btn ghost" @tap="openCategoryModal()">新增分类</button>
      <button class="toolbar-btn" @tap="openFruitModal()">新增报价</button>
    </view>

    <view class="manager-card">
      <scroll-view scroll-y class="category-menu">
        <view class="menu-item" :class="{ active: activeCategoryId === 'all' }" @tap="setActiveCategory('all')">
          <text>全部报价</text>
        </view>
        <view
          v-for="category in categories"
          :key="category.id"
          class="menu-item"
          :class="{ active: Number(activeCategoryId) === category.id, muted: !category.is_active }"
          @tap="setActiveCategory(category.id)"
        >
          <image v-if="category.icon_url" class="menu-icon-img" :src="category.icon_url" mode="aspectFill" />
          <image v-else-if="categoryIconPath(category.icon)" class="menu-icon-img" :src="categoryIconPath(category.icon)" mode="aspectFit" />
          <text>{{ category.name }}</text>
        </view>
        <view class="menu-item manage" :class="{ active: activeCategoryId === 'category_manager' }" @tap="setActiveCategory('category_manager')">分类管理</view>
      </scroll-view>

      <view class="list-panel">
        <view v-if="loading" class="empty">正在加载...</view>

        <view v-else-if="activeCategoryId === 'category_manager'">
          <view class="panel-head">
            <text class="panel-title">分类管理</text>
            <button class="mini-btn" @tap="openCategoryModal()">新增</button>
          </view>
          <view v-if="!categories.length" class="empty">还没有分类，点击新增分类开始管理。</view>
          <view v-for="category in categories" :key="category.id" class="category-row" @tap="openCategoryModal(category)">
            <view class="category-main">
              <view v-if="category.icon_url" class="category-icon">
                <image class="category-icon-img" :src="category.icon_url" mode="aspectFill" />
              </view>
              <view v-else-if="categoryIconPath(category.icon)" class="category-icon">
                <image class="category-icon-img" :src="categoryIconPath(category.icon)" mode="aspectFit" />
              </view>
              <view>
                <view class="category-name">{{ category.name }}</view>
                <view class="category-meta">
                  排序 {{ category.sort_order }} · {{ category.is_active ? '前台显示' : '已停用' }} · {{ category.icon_url ? '自定义图片' : (categoryIconLabel(category.icon) || '未选图标') }}
                </view>
              </view>
            </view>
            <text class="edit-text">编辑</text>
          </view>
        </view>

        <view v-else>
          <view class="panel-head">
            <text class="panel-title">报价列表</text>
            <text class="panel-count">{{ filteredFruits.length }} 个</text>
          </view>
          <view v-if="!categories.length" class="empty">请先新增分类，再添加水果报价。</view>
          <view v-else-if="!filteredFruits.length" class="empty">当前分类暂无报价。</view>
          <view v-for="fruit in filteredFruits" :key="fruit.id" class="fruit-row" @tap="openFruitModal(fruit)">
            <image v-if="fruit.image_urls?.[0] || fruit.image_url" class="fruit-img" :src="fruit.image_urls?.[0] || fruit.image_url" mode="aspectFill" />
            <view v-else class="fruit-img placeholder">果</view>
            <view class="fruit-main">
              <view class="fruit-head">
                <text class="fruit-name">{{ fruit.name }}</text>
                <text class="stock">{{ statusLabel(fruit.stock_status) }}</text>
              </view>
              <view class="fruit-info">{{ fruit.category }} · {{ fruit.origin || '未填产地' }} · {{ fruit.spec }}</view>
              <view class="fruit-price">普通 ¥{{ money(fruit.quote?.normal_price) }} / 认证 ¥{{ money(fruit.quote?.verified_price) }}</view>
              <view class="fruit-tags">
                <text v-if="fruit.is_recommended" class="tag">推荐</text>
                <text class="tag light">起订 {{ fruit.quote?.min_order_quantity }}{{ fruit.unit }}</text>
              </view>
            </view>
          </view>
        </view>
      </view>
    </view>

    <view v-if="fruitModalVisible" class="modal-mask" @tap="closeFruitModal">
      <view class="modal-card large" @tap.stop>
        <view class="modal-head">
          <text class="modal-title">{{ editingFruitId ? '编辑报价' : '新增报价' }}</text>
          <text class="modal-close" @tap="closeFruitModal">×</text>
        </view>
        <scroll-view scroll-y class="modal-body">
          <input v-model="form.name" class="input" placeholder="水果名称" />
          <picker :range="categoryNames" :value="categoryPickerIndex" @change="changeFruitCategory">
            <view class="picker">分类：{{ selectedCategoryName }}</view>
          </picker>
          <input v-model="form.origin" class="input" placeholder="产地" />
          <input v-model="form.spec" class="input" placeholder="规格" />
          <input v-model="form.unit" class="input" placeholder="单位，如斤/箱" />
          <input v-model="form.normal_price" class="input" type="digit" placeholder="普通价" />
          <input v-model="form.verified_price" class="input" type="digit" placeholder="认证优惠价" />
          <input v-model="form.min_order_quantity" class="input" type="digit" placeholder="起订量" />
          <input v-model="form.grade" class="input" placeholder="等级" />
          <input v-model="form.note" class="input" placeholder="备注" />
          <view class="image-section">
            <view class="image-head">
              <text>封面图</text>
              <button class="upload-btn" @tap="chooseCoverImage">{{ form.image_url ? '更换封面' : '上传封面' }}</button>
            </view>
            <view class="cover-row">
              <view v-if="form.image_url" class="cover-wrap">
                <image class="cover-image" :src="form.image_url" mode="aspectFill" @tap="previewCoverImage" />
                <text class="remove" @tap.stop="removeCoverImage">×</text>
              </view>
              <view v-else class="cover-empty" @tap="chooseCoverImage">+ 添加封面图</view>
              <view class="image-help">封面用于首页、分类列表和详情页顶部主图。</view>
            </view>
          </view>
          <view class="image-section">
            <view class="image-head">
              <text>详情图片（{{ form.detail_image_urls.length }}/{{ maxDetailImages }}）</text>
              <button class="upload-btn" @tap="chooseDetailImages">多选上传</button>
            </view>
            <view class="image-help block">像淘宝详情页一样纵向展示，建议上传果面、包装、装车、产地实拍等图片。</view>
            <view class="image-list">
              <view v-for="(url, index) in form.detail_image_urls" :key="url" class="image-wrap">
                <image class="fruit-image" :src="url" mode="aspectFill" @tap="previewDetailImages(url)" />
                <text class="image-order">{{ index + 1 }}</text>
                <text class="remove" @tap.stop="removeDetailImage(index)">×</text>
              </view>
              <view v-if="form.detail_image_urls.length === 0" class="image-empty" @tap="chooseDetailImages">+ 添加详情图</view>
            </view>
          </view>
          <view class="switch-row">
            <text>推荐展示</text>
            <switch :checked="form.is_recommended" @change="form.is_recommended = $event.detail.value" />
          </view>
          <picker :range="stockValues.map(statusLabel)" :value="stockPickerIndex" @change="changeStock">
            <view class="picker">库存状态：{{ statusLabel(form.stock_status) }}</view>
          </picker>
        </scroll-view>
        <button class="save" :loading="saving" @tap="saveFruit">保存报价</button>
      </view>
    </view>

    <view v-if="categoryModalVisible" class="modal-mask" @tap="closeCategoryModal">
      <view class="modal-card" @tap.stop>
        <view class="modal-head">
          <text class="modal-title">{{ editingCategoryId ? '编辑分类' : '新增分类' }}</text>
          <text class="modal-close" @tap="closeCategoryModal">×</text>
        </view>
        <input v-model="categoryForm.name" class="input" placeholder="分类名称，如苹果类" />
        <view class="icon-field">
          <view class="icon-preview" v-if="categoryForm.icon_url" @tap.stop="previewCategoryIcon">
            <image class="icon-preview-img" :src="categoryForm.icon_url" mode="aspectFill" />
            <text class="icon-clear" @tap.stop="clearCategoryIconUrl">×</text>
          </view>
          <view v-else-if="selectedCategoryIconPath" class="icon-preview" @tap="openIconPicker">
            <image class="icon-preview-img" :src="selectedCategoryIconPath" mode="aspectFit" />
          </view>
          <view class="icon-field-main">
            <view class="icon-field-title">分类图标</view>
            <view class="icon-field-sub">{{ selectedCategoryIconLabel || '未选择，用户端只显示文字' }}</view>
          </view>
          <view class="icon-actions">
            <button class="icon-upload-btn" @tap.stop="chooseCategoryIcon">上传图片</button>
            <button class="icon-select-btn" @tap.stop="openIconPicker">选择图标</button>
          </view>
        </view>
        <input v-model="categoryForm.sort_order" class="input" type="number" placeholder="排序，数字越小越靠前" />
        <view class="switch-row">
          <text>前台显示</text>
          <switch :checked="categoryForm.is_active" @change="categoryForm.is_active = $event.detail.value" />
        </view>
        <button class="save" :loading="saving" @tap="saveCategory">保存分类</button>
      </view>
    </view>

    <view v-if="iconPickerVisible" class="modal-mask" @tap="closeIconPicker">
      <view class="icon-picker-card" @tap.stop>
        <view class="modal-head">
          <text class="modal-title">选择分类图标</text>
          <text class="modal-close" @tap="closeIconPicker">×</text>
        </view>
        <view class="picker-actions">
          <button class="clear-icon-btn" @tap="clearCategoryIcon">不使用图标</button>
        </view>
        <scroll-view scroll-y class="icon-picker-scroll">
          <view class="icon-section-title">推荐水果</view>
          <view class="icon-grid">
            <view
              v-for="icon in recommendedCategoryIcons"
              :key="icon.id"
              class="icon-option"
              :class="{ active: categoryForm.icon === icon.id }"
              @tap="selectCategoryIcon(icon)"
            >
              <image class="icon-option-img" :src="icon.path" mode="aspectFit" />
              <text class="icon-option-name">{{ icon.label }}</text>
            </view>
          </view>
          <view class="icon-section-title">全部水果</view>
          <view class="icon-grid">
            <view
              v-for="icon in allCategoryIcons"
              :key="`all-${icon.id}`"
              class="icon-option"
              :class="{ active: categoryForm.icon === icon.id }"
              @tap="selectCategoryIcon(icon)"
            >
              <image class="icon-option-img" :src="icon.path" mode="aspectFit" />
              <text class="icon-option-name">{{ icon.label }}</text>
            </view>
          </view>
        </scroll-view>
      </view>
    </view>
  </view>
</template>

<style scoped>
.page { min-height: 100vh; padding: 24rpx; background: #f5f8ef; box-sizing: border-box; }
.admin-nav { display: flex; gap: 10rpx; margin-bottom: 20rpx; }
.nav-button { flex: 1; height: 70rpx; line-height: 70rpx; border-radius: 999rpx; color: #2f4b21; background: #fff; font-size: 24rpx; }
.nav-button.active { color: #fff; background: #2f6b23; }
.toolbar { display: grid; grid-template-columns: 1fr 156rpx 156rpx; gap: 12rpx; align-items: center; margin-bottom: 18rpx; }
.search { height: 70rpx; padding: 0 22rpx; border-radius: 999rpx; background: #fff; color: #173b16; font-size: 25rpx; box-sizing: border-box; }
.toolbar-btn { height: 70rpx; line-height: 70rpx; border-radius: 999rpx; color: #fff; background: #ffb700; font-size: 24rpx; }
.toolbar-btn.ghost { color: #2f6b23; background: #fff; }
.manager-card { display: flex; min-height: 760rpx; overflow: hidden; border-radius: 26rpx; background: #fff; box-shadow: 0 10rpx 26rpx rgba(73,83,47,.08); }
.category-menu { flex-shrink: 0; width: 176rpx; max-height: 980rpx; border-right: 1rpx solid #edf2e6; background: #fbfcf8; }
.menu-item { display: flex; align-items: center; gap: 8rpx; padding: 28rpx 18rpx; color: #48613b; font-size: 25rpx; line-height: 1.35; }
.menu-icon-img { flex-shrink: 0; width: 30rpx; height: 30rpx; }
.menu-item.active { color: #2f6b23; font-weight: 900; background: #ecf7df; }
.menu-item.muted { color: #a6b09c; }
.menu-item.manage { margin-top: 16rpx; color: #df5d00; }
.list-panel { flex: 1; min-width: 0; padding: 22rpx; }
.panel-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 18rpx; }
.panel-title { color: #173b16; font-size: 31rpx; font-weight: 900; }
.panel-count { color: #768273; font-size: 24rpx; }
.mini-btn { width: 112rpx; height: 54rpx; line-height: 54rpx; border-radius: 999rpx; color: #fff; background: #2f6b23; font-size: 23rpx; }
.empty { padding: 80rpx 20rpx; text-align: center; color: #768273; font-size: 26rpx; line-height: 1.5; }
.fruit-row, .category-row { display: flex; gap: 18rpx; padding: 20rpx 0; border-bottom: 1rpx solid #edf2e6; }
.category-row { align-items: center; justify-content: space-between; }
.category-main { display: flex; align-items: center; gap: 16rpx; min-width: 0; }
.category-icon { display: flex; align-items: center; justify-content: center; flex-shrink: 0; width: 58rpx; height: 58rpx; border-radius: 18rpx; background: #f5f8ef; }
.category-icon-img { width: 42rpx; height: 42rpx; }
.fruit-img { flex-shrink: 0; width: 126rpx; height: 126rpx; border-radius: 18rpx; background: #f5f8ef; }
.fruit-img.placeholder { display: flex; align-items: center; justify-content: center; color: #2f6b23; font-size: 36rpx; font-weight: 900; }
.fruit-main { flex: 1; min-width: 0; }
.fruit-head { display: flex; align-items: center; justify-content: space-between; gap: 16rpx; }
.fruit-name, .category-name { color: #173b16; font-size: 29rpx; font-weight: 900; }
.stock, .edit-text { color: #df5d00; font-size: 24rpx; font-weight: 800; }
.fruit-info, .category-meta { margin-top: 8rpx; color: #60715c; font-size: 24rpx; line-height: 1.45; }
.fruit-price { margin-top: 10rpx; color: #df5d00; font-size: 27rpx; font-weight: 900; }
.fruit-tags { display: flex; gap: 10rpx; margin-top: 10rpx; }
.tag { padding: 4rpx 12rpx; border-radius: 999rpx; color: #fff; background: #2f6b23; font-size: 21rpx; }
.tag.light { color: #60715c; background: #f0f5ea; }
.modal-mask { position: fixed; z-index: 99; left: 0; right: 0; top: 0; bottom: 0; display: flex; align-items: flex-end; justify-content: center; background: rgba(16, 28, 12, .45); }
.modal-card { width: 100%; max-height: 88vh; padding: 28rpx 28rpx calc(96rpx + env(safe-area-inset-bottom)); border-radius: 34rpx 34rpx 0 0; background: #fff; box-sizing: border-box; }
.modal-card.large { height: 88vh; }
.modal-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 18rpx; }
.modal-title { color: #173b16; font-size: 34rpx; font-weight: 900; }
.modal-close { width: 64rpx; height: 64rpx; line-height: 60rpx; text-align: center; color: #60715c; font-size: 44rpx; }
.modal-body { max-height: calc(88vh - 188rpx); }
.input, .picker { min-height: 74rpx; margin-top: 14rpx; padding: 0 20rpx; border-radius: 18rpx; color: #48613b; background: #f5f8ef; font-size: 26rpx; box-sizing: border-box; }
.picker { display: flex; align-items: center; }
.icon-field { display: flex; align-items: center; gap: 16rpx; min-height: 88rpx; margin-top: 14rpx; padding: 16rpx 20rpx; border-radius: 18rpx; background: #f5f8ef; box-sizing: border-box; }
.icon-preview { display: flex; align-items: center; justify-content: center; flex-shrink: 0; width: 60rpx; height: 60rpx; border-radius: 18rpx; background: #fff; position: relative; overflow: hidden; }
.icon-preview-img { width: 60rpx; height: 60rpx; }
.icon-clear { position: absolute; right: -8rpx; top: -8rpx; display: flex; align-items: center; justify-content: center; width: 34rpx; height: 34rpx; border-radius: 50%; color: #fff; background: #ef4444; font-size: 28rpx; }
.icon-field-main { flex: 1; min-width: 0; }
.icon-field-title { color: #173b16; font-size: 26rpx; font-weight: 800; }
.icon-field-sub { margin-top: 6rpx; color: #768273; font-size: 23rpx; }
.icon-actions { display: flex; flex-direction: column; gap: 8rpx; }
.icon-upload-btn,
.icon-select-btn { height: 56rpx; line-height: 56rpx; padding: 0 16rpx; border-radius: 999rpx; font-size: 22rpx; font-weight: 800; }
.icon-upload-btn { color: #fff; background: #ffb700; }
.icon-select-btn { color: #2f6b23; background: #eef7e6; }
.icon-upload-btn::after,
.icon-select-btn::after { border: none; }
.icon-picker-card { width: 100%; height: 74vh; padding: 28rpx 28rpx calc(42rpx + env(safe-area-inset-bottom)); border-radius: 34rpx 34rpx 0 0; background: #fff; box-sizing: border-box; }
.picker-actions { display: flex; justify-content: flex-end; margin-bottom: 14rpx; }
.clear-icon-btn { width: 180rpx; height: 58rpx; line-height: 58rpx; border-radius: 999rpx; color: #60715c; background: #eef1ea; font-size: 24rpx; }
.icon-picker-scroll { height: calc(74vh - 178rpx); }
.icon-section-title { margin: 18rpx 0 14rpx; color: #173b16; font-size: 28rpx; font-weight: 900; }
.icon-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14rpx; }
.icon-option { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 140rpx; padding: 14rpx 8rpx; border: 2rpx solid transparent; border-radius: 20rpx; background: #f5f8ef; box-sizing: border-box; }
.icon-option.active { border-color: #ffb700; background: #fff7df; }
.icon-option-img { width: 56rpx; height: 56rpx; }
.icon-option-name { margin-top: 10rpx; color: #48613b; font-size: 21rpx; text-align: center; line-height: 1.2; }
.switch-row { display: flex; justify-content: space-between; align-items: center; margin-top: 16rpx; color: #48613b; font-size: 26rpx; }
.image-section { margin-top: 18rpx; }
.image-head { display: flex; align-items: center; justify-content: space-between; color: #173b16; font-size: 27rpx; font-weight: 800; }
.upload-btn { width: 150rpx; height: 58rpx; line-height: 58rpx; border-radius: 999rpx; color: #fff; background: #ffb700; font-size: 24rpx; }
.cover-row { display: flex; align-items: center; gap: 18rpx; margin-top: 14rpx; }
.cover-wrap { position: relative; width: 220rpx; height: 176rpx; }
.cover-image { width: 220rpx; height: 176rpx; border-radius: 18rpx; background: #f5f8ef; }
.cover-empty { display: flex; align-items: center; justify-content: center; width: 220rpx; height: 176rpx; border: 2rpx dashed #ffcf68; border-radius: 18rpx; color: #ff9f00; font-size: 25rpx; background: #fffaf0; }
.image-help { flex: 1; color: #768273; font-size: 23rpx; line-height: 1.45; }
.image-help.block { margin-top: 10rpx; }
.image-list { display: flex; flex-wrap: wrap; gap: 14rpx; margin-top: 14rpx; }
.image-wrap { position: relative; width: 142rpx; height: 142rpx; }
.fruit-image { width: 142rpx; height: 142rpx; border-radius: 16rpx; background: #f5f8ef; }
.remove { position: absolute; right: -8rpx; top: -8rpx; display: flex; align-items: center; justify-content: center; width: 34rpx; height: 34rpx; border-radius: 50%; color: #fff; background: #ef4444; font-size: 28rpx; }
.image-order { position: absolute; left: 8rpx; top: 8rpx; min-width: 30rpx; height: 30rpx; line-height: 30rpx; border-radius: 999rpx; text-align: center; color: #fff; background: rgba(47, 107, 35, .86); font-size: 20rpx; }
.image-empty { display: flex; align-items: center; justify-content: center; width: 180rpx; height: 142rpx; border: 2rpx dashed #ffcf68; border-radius: 16rpx; color: #ff9f00; font-size: 24rpx; background: #fffaf0; }
.save { margin-top: 24rpx; margin-bottom: 36rpx; height: 76rpx; line-height: 76rpx; border-radius: 999rpx; color: #fff; background: #2f6b23; font-size: 28rpx; font-weight: 800; }
.clear-icon-btn::after { border: none; }
</style>
