<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createCategory, createFruit, listCategories, listPublicFruits, updateCategory, updateFruit, uploadImage } from '../api'
import { STOCK_STATUSES, money, qtyText, statusLabel, statusTone } from '../utils/format'

const loading = ref(false)
const fruits = ref([])
const categories = ref([])
const activeCategory = ref('all')
const keyword = ref('')

const fruitDialog = ref(false)
const fruitForm = reactive(blankFruit())
const fruitSaving = ref(false)

const categoryDialog = ref(false)
const categoryForm = reactive(blankCategory())
const categorySaving = ref(false)

function blankFruit() {
  return {
    id: null,
    name: '',
    category_id: null,
    origin: '',
    spec: '',
    unit: '斤',
    stock_status: 'in_stock',
    is_recommended: false,
    normal_price: 1,
    verified_price: 1,
    grade: '一级',
    min_order_quantity: 1,
    note: '',
    image_url: '',
    detail_image_urls: [],
  }
}

function blankCategory() {
  return { id: null, name: '', icon: '', icon_url: '', sort_order: 0, is_active: true }
}

const filteredFruits = computed(() => {
  const word = keyword.value.trim().toLowerCase()
  return fruits.value.filter((fruit) => {
    if (activeCategory.value !== 'all' && String(fruit.category_id) !== String(activeCategory.value)) return false
    if (!word) return true
    return [fruit.name, fruit.origin, fruit.spec].join(' ').toLowerCase().includes(word)
  })
})

async function load() {
  loading.value = true
  try {
    const [fruitList, categoryList] = await Promise.all([listPublicFruits({}), listCategories()])
    fruits.value = fruitList
    categories.value = categoryList
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

function openFruit(row) {
  if (!categories.value.length) {
    ElMessage.warning('请先新增分类')
    return
  }
  Object.assign(fruitForm, row ? {
    ...row,
    origin: row.origin || '',
    note: row.quote?.note || '',
    normal_price: Number(row.quote?.normal_price ?? 1),
    verified_price: Number(row.quote?.verified_price ?? 1),
    grade: row.quote?.grade || '一级',
    min_order_quantity: Number(row.quote?.min_order_quantity ?? 1),
    detail_image_urls: [...(row.detail_image_urls || [])],
  } : blankFruit())
  if (!row) fruitForm.category_id = categories.value[0]?.id ?? null
  fruitDialog.value = true
}

async function saveFruit() {
  if (!fruitForm.name || !fruitForm.category_id || !fruitForm.spec) {
    ElMessage.warning('请补全水果名称、分类和规格')
    return
  }
  if (!(Number(fruitForm.normal_price) > 0) || !(Number(fruitForm.verified_price) > 0) || !(Number(fruitForm.min_order_quantity) > 0)) {
    ElMessage.warning('价格与起购量必须大于 0')
    return
  }
  const payload = {
    name: fruitForm.name,
    category_id: Number(fruitForm.category_id),
    image_url: fruitForm.image_url || null,
    image_urls: fruitForm.image_url ? [fruitForm.image_url] : [],
    detail_image_urls: fruitForm.detail_image_urls || [],
    origin: fruitForm.origin || null,
    spec: fruitForm.spec,
    unit: fruitForm.unit || '斤',
    stock_status: fruitForm.stock_status,
    is_recommended: !!fruitForm.is_recommended,
    normal_price: Number(fruitForm.normal_price),
    verified_price: Number(fruitForm.verified_price),
    grade: fruitForm.grade || '一级',
    min_order_quantity: Number(fruitForm.min_order_quantity),
    note: fruitForm.note || null,
  }
  fruitSaving.value = true
  try {
    if (fruitForm.id) await updateFruit(fruitForm.id, payload)
    else await createFruit(payload)
    ElMessage.success('已保存')
    fruitDialog.value = false
    await load()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    fruitSaving.value = false
  }
}

async function uploadFruitCover(options) {
  try {
    const result = await uploadImage(options.file)
    fruitForm.image_url = result.url
  } catch (error) {
    ElMessage.error(error.message)
  }
}

async function uploadFruitDetail(options) {
  try {
    const result = await uploadImage(options.file)
    fruitForm.detail_image_urls = [...fruitForm.detail_image_urls, result.url]
  } catch (error) {
    ElMessage.error(error.message)
  }
}

function openCategory(row) {
  Object.assign(categoryForm, row ? { ...row } : { ...blankCategory(), sort_order: (categories.value.length + 1) * 10 })
  categoryDialog.value = true
}

async function saveCategory() {
  if (!categoryForm.name.trim()) {
    ElMessage.warning('分类名称必填')
    return
  }
  const payload = {
    name: categoryForm.name.trim(),
    icon: categoryForm.icon || null,
    icon_url: categoryForm.icon_url || null,
    sort_order: Number(categoryForm.sort_order) || 0,
    is_active: !!categoryForm.is_active,
  }
  categorySaving.value = true
  try {
    if (categoryForm.id) await updateCategory(categoryForm.id, payload)
    else await createCategory(payload)
    ElMessage.success('分类已保存')
    categoryDialog.value = false
    await load()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    categorySaving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page layout">
    <el-card shadow="never" class="side">
      <template #header>
        <div class="card-head">
          <span>分类</span>
          <el-button size="small" @click="openCategory(null)">新增分类</el-button>
        </div>
      </template>
      <div :class="['cat', { on: activeCategory === 'all' }]" @click="activeCategory = 'all'">
        全部报价（{{ fruits.length }}）
      </div>
      <div
        v-for="item in categories"
        :key="item.id"
        :class="['cat', { on: String(activeCategory) === String(item.id), off: !item.is_active }]"
        @click="activeCategory = item.id"
      >
        <el-image v-if="item.icon_url" :src="item.icon_url" fit="cover" class="cat-icon" />
        <span>{{ item.name }}</span>
        <el-button link size="small" class="edit" @click.stop="openCategory(item)">编辑</el-button>
      </div>
    </el-card>

    <div class="content" v-loading="loading">
      <div class="page-toolbar">
        <el-input v-model="keyword" placeholder="搜索名称/产地/规格" clearable style="width: 220px" />
        <div class="grow"></div>
        <el-button @click="load">刷新</el-button>
        <el-button type="primary" @click="openFruit(null)">新增报价</el-button>
      </div>
      <el-table :data="filteredFruits" border>
        <el-table-column label="图片" width="80">
          <template #default="{ row }">
            <el-image v-if="row.image_url" :src="row.image_url" fit="cover" class="thumb" />
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="水果" min-width="150">
          <template #default="{ row }">
            <div>{{ row.name }}<el-tag v-if="row.is_recommended" size="small" type="danger" class="tag">推荐</el-tag></div>
            <div class="muted">{{ row.category }} · {{ row.origin || '未填产地' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="规格" min-width="130">
          <template #default="{ row }">{{ row.spec }} / {{ row.unit }}</template>
        </el-table-column>
        <el-table-column label="价格" min-width="170">
          <template #default="{ row }">
            <div>普通 ¥{{ money(row.quote?.normal_price) }} · 认证 ¥{{ money(row.quote?.verified_price) }}</div>
            <div class="muted">{{ row.quote?.grade }} · 起购 {{ qtyText(row.quote?.min_order_quantity) }}{{ row.unit }}</div>
          </template>
        </el-table-column>
        <el-table-column label="库存" width="110">
          <template #default="{ row }"><el-tag :type="statusTone(row.stock_status)">{{ statusLabel(row.stock_status) }}</el-tag></template>
        </el-table-column>
        <el-table-column label="详情图" width="90">
          <template #default="{ row }">{{ (row.detail_image_urls || []).length }} 张</template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }"><el-button size="small" @click="openFruit(row)">编辑</el-button></template>
        </el-table-column>
        <template #empty><span class="muted">暂无水果报价</span></template>
      </el-table>
    </div>

    <el-dialog v-model="fruitDialog" :title="fruitForm.id ? '编辑报价' : '新增报价'" width="640px">
      <el-form label-width="96px">
        <el-form-item label="名称" required>
          <el-input v-model="fruitForm.name" placeholder="如 红颜草莓" />
        </el-form-item>
        <el-form-item label="分类" required>
          <el-select v-model="fruitForm.category_id" style="width: 100%">
            <el-option v-for="item in categories" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="规格" required>
              <el-input v-model="fruitForm.spec" placeholder="如 500g/盒" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="单位">
              <el-input v-model="fruitForm.unit" placeholder="斤" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="普通价" required>
              <el-input-number v-model="fruitForm.normal_price" :min="0.01" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="认证价" required>
              <el-input-number v-model="fruitForm.verified_price" :min="0.01" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="等级">
              <el-input v-model="fruitForm.grade" placeholder="一级" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="起购量" required>
              <el-input-number v-model="fruitForm.min_order_quantity" :min="0.01" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="产地">
          <el-input v-model="fruitForm.origin" placeholder="选填" />
        </el-form-item>
        <el-form-item label="库存状态">
          <el-radio-group v-model="fruitForm.stock_status">
            <el-radio v-for="item in STOCK_STATUSES" :key="item" :value="item">{{ statusLabel(item) }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="首页推荐">
          <el-switch v-model="fruitForm.is_recommended" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="fruitForm.note" type="textarea" :rows="2" placeholder="选填，展示在商品详情" />
        </el-form-item>
        <el-form-item label="封面图">
          <div class="upload">
            <el-upload :show-file-list="false" accept="image/*" :http-request="uploadFruitCover">
              <el-button size="small">上传封面</el-button>
            </el-upload>
            <el-image v-if="fruitForm.image_url" :src="fruitForm.image_url" fit="cover" class="thumb" preview-teleported :preview-src-list="[fruitForm.image_url]" />
            <el-button v-if="fruitForm.image_url" link type="danger" @click="fruitForm.image_url = ''">移除</el-button>
          </div>
        </el-form-item>
        <el-form-item label="详情图">
          <div class="upload">
            <el-upload :show-file-list="false" accept="image/*" multiple :http-request="uploadFruitDetail">
              <el-button size="small">上传详情图</el-button>
            </el-upload>
            <div v-for="(url, index) in fruitForm.detail_image_urls" :key="url" class="detail-item">
              <el-image :src="url" fit="cover" class="thumb" preview-teleported :preview-src-list="fruitForm.detail_image_urls" :initial-index="index" />
              <el-button link type="danger" size="small" @click="fruitForm.detail_image_urls.splice(index, 1)">删除</el-button>
            </div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="fruitDialog = false">取消</el-button>
        <el-button type="primary" :loading="fruitSaving" @click="saveFruit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="categoryDialog" :title="categoryForm.id ? '编辑分类' : '新增分类'" width="460px">
      <el-form label-width="90px">
        <el-form-item label="名称" required>
          <el-input v-model="categoryForm.name" placeholder="如 浆果类" />
        </el-form-item>
        <el-form-item label="图标名">
          <el-input v-model="categoryForm.icon" placeholder="选填，内置图标 id" />
        </el-form-item>
        <el-form-item label="图标图片">
          <div class="upload">
            <el-upload :show-file-list="false" accept="image/*" :http-request="async (options) => { categoryForm.icon_url = (await uploadImage(options.file)).url }">
              <el-button size="small">上传图标</el-button>
            </el-upload>
            <el-image v-if="categoryForm.icon_url" :src="categoryForm.icon_url" fit="cover" class="cat-icon" />
            <el-button v-if="categoryForm.icon_url" link type="danger" @click="categoryForm.icon_url = ''">移除</el-button>
          </div>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="categoryForm.sort_order" :min="0" />
          <span class="muted sort-tip">越小越靠前</span>
        </el-form-item>
        <el-form-item label="前台显示">
          <el-switch v-model="categoryForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="categoryDialog = false">取消</el-button>
        <el-button type="primary" :loading="categorySaving" @click="saveCategory">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.side {
  width: 220px;
  flex: 0 0 220px;
}

.content {
  flex: 1 1 auto;
  min-width: 0;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.cat {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 9px 8px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.cat:hover {
  background: #f5f7fa;
}

.cat.on {
  color: #fff;
  background: #ffb700;
}

.cat.off {
  color: #b1b3b8;
}

.cat .edit {
  margin-left: auto;
}

.thumb {
  width: 46px;
  height: 46px;
  border-radius: 6px;
}

.cat-icon {
  width: 22px;
  height: 22px;
  border-radius: 4px;
}

.tag {
  margin-left: 6px;
}

.upload {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.sort-tip {
  margin-left: 8px;
  font-size: 12px;
}
</style>
