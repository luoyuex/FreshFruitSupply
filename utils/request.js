// export const API_BASE_URL = 'https://zhiyingai.online/apigmap'
// export const API_BASE_URL = 'http://127.0.0.1:8000/api'
export const API_BASE_URL = 'http://192.168.71.116:8000/api'

function getAdminToken() {
  return uni.getStorageSync('admin_token') || ''
}

function getCustomerToken() {
  return uni.getStorageSync('customer_token') || ''
}

function uploadErrorMessage(data, fallback) {
  try {
    const parsed = typeof data === 'string' ? JSON.parse(data) : data
    const message = parsed?.detail || parsed?.message
    return Array.isArray(message) ? message.map((item) => item.msg).join('；') : (message || fallback)
  } catch (error) {
    return data || fallback
  }
}

function getFileSize(filePath) {
  if (!filePath || filePath.startsWith('http')) return Promise.resolve(0)
  return new Promise((resolve) => {
    uni.getFileInfo({
      filePath,
      success: (res) => resolve(Number(res.size || 0)),
      fail: () => resolve(0),
    })
  })
}

export async function compressUploadImage(filePath, quality = 60) {
  if (!filePath || filePath.startsWith('http')) return filePath
  if (!uni.compressImage) return filePath

  const originalSize = await getFileSize(filePath)
  return new Promise((resolve) => {
    uni.compressImage({
      src: filePath,
      quality,
      success: async (res) => {
        const compressedPath = res.tempFilePath || filePath
        const compressedSize = await getFileSize(compressedPath)
        if (originalSize && compressedSize && compressedSize >= originalSize) {
          resolve(filePath)
          return
        }
        resolve(compressedPath)
      },
      fail: () => resolve(filePath),
    })
  })
}

export function request(options) {
  const { url, method = 'GET', data, admin = false, headers = {} } = options
  const requestHeaders = { ...headers }

  if (admin && getAdminToken()) {
    requestHeaders.Authorization = `Bearer ${getAdminToken()}`
  } else if (!admin && getCustomerToken()) {
    requestHeaders.Authorization = `Bearer ${getCustomerToken()}`
  }

  return new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE_URL}${url}`,
      method,
      data,
      header: requestHeaders,
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
          return
        }
        const message = res.data?.detail || res.data?.message || '请求失败'
        if (admin && res.statusCode === 401) {
          uni.removeStorageSync('admin_token')
          uni.removeStorageSync('admin_user')
          uni.removeStorageSync('admin_permissions')
        }
        reject(new Error(Array.isArray(message) ? message.map((item) => item.msg).join('；') : message))
      },
      fail: (err) => reject(new Error(err.errMsg || '网络连接失败')),
    })
  })
}

export async function uploadVerification({ formData, filePath }) {
  const uploadPath = await compressUploadImage(filePath, 60)
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${API_BASE_URL}/customers/verification`,
      filePath: uploadPath,
      name: 'images',
      formData,
      header: getCustomerToken() ? { Authorization: `Bearer ${getCustomerToken()}` } : {},
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          try {
            resolve(JSON.parse(res.data))
          } catch (error) {
            resolve(res.data)
          }
          return
        }
        reject(new Error(uploadErrorMessage(res.data, '上传失败')))
      },
      fail: (err) => reject(new Error(err.errMsg || '上传失败')),
    })
  })
}

export async function uploadAdminImage(filePath) {
  const uploadPath = await compressUploadImage(filePath, 60)
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${API_BASE_URL}/admin/uploads`,
      filePath: uploadPath,
      name: 'file',
      header: getAdminToken() ? { Authorization: `Bearer ${getAdminToken()}` } : {},
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          try {
            resolve(JSON.parse(res.data))
          } catch (error) {
            resolve(res.data)
          }
          return
        }
        reject(new Error(uploadErrorMessage(res.data, '图片上传失败')))
      },
      fail: (err) => reject(new Error(err.errMsg || '图片上传失败')),
    })
  })
}

export async function uploadAvatar(filePath) {
  const uploadPath = await compressUploadImage(filePath, 70)
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${API_BASE_URL}/customers/avatar`,
      filePath: uploadPath,
      name: 'avatar',
      header: getCustomerToken() ? { Authorization: `Bearer ${getCustomerToken()}` } : {},
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          try {
            resolve(JSON.parse(res.data))
          } catch (error) {
            resolve(res.data)
          }
          return
        }
        reject(new Error(uploadErrorMessage(res.data, '头像上传失败')))
      },
      fail: (err) => reject(new Error(err.errMsg || '头像上传失败')),
    })
  })
}
