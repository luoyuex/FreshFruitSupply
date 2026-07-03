import { computed, ref, shallowRef } from 'vue'
import { request } from '../utils/request.js'

export function useFruitQuotes() {
  const fruits = ref([])
  const categoryItems = ref([])
  const loading = shallowRef(false)
  const error = shallowRef('')
  const keyword = shallowRef('')
  const activeCategory = shallowRef('全部')

  const categories = computed(() => {
    if (!categoryItems.value.length) return []
    return ['全部', ...categoryItems.value.map((item) => item.name)]
  })

  const visibleFruits = computed(() => {
    const text = keyword.value.trim()
    return fruits.value.filter((item) => {
      const matchesCategory = text ? true : (activeCategory.value === '全部' || item.category === activeCategory.value)
      const matchesKeyword = !text || item.name.includes(text) || item.origin?.includes(text)
      return matchesCategory && matchesKeyword
    })
  })

  async function loadFruits() {
    loading.value = true
    error.value = ''
    try {
      const [categoryData, fruitData] = await Promise.all([
        request({ url: '/categories' }),
        request({ url: '/fruits' }),
      ])
      categoryItems.value = categoryData
      fruits.value = fruitData
      if (categories.value.length && !categories.value.includes(activeCategory.value)) {
        activeCategory.value = '全部'
      }
    } catch (err) {
      error.value = err.message
      categoryItems.value = []
      fruits.value = []
    } finally {
      loading.value = false
    }
  }

  return { fruits, categoryItems, loading, error, keyword, activeCategory, categories, visibleFruits, loadFruits }
}
