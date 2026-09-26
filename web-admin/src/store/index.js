import { createStore } from 'vuex'
import { login as loginRequest, fetchMe } from '../api'
import { clearToken, readToken, setToken } from '../api/request'
import { ADMIN_NAV } from '../utils/format'

export default createStore({
  state() {
    return {
      token: readToken(),
      admin: null,
      permissions: [],
      ready: false,
    }
  },
  getters: {
    isLoggedIn: (state) => Boolean(state.token && state.admin),
    permissions: (state) => state.permissions,
    navItems: (state) => ADMIN_NAV.filter((item) => state.permissions.includes(item.key)),
    can: (state) => (key) => state.permissions.includes(key),
  },
  mutations: {
    setSession(state, { token, admin, permissions }) {
      if (token) {
        state.token = token
        setToken(token)
      }
      if (admin) state.admin = admin
      state.permissions = permissions || []
    },
    clearSession(state) {
      state.token = ''
      state.admin = null
      state.permissions = []
      clearToken()
    },
    setReady(state, value) {
      state.ready = value
    },
  },
  actions: {
    async login({ commit }, payload) {
      const data = await loginRequest(payload)
      commit('setSession', { token: data.access_token, admin: data.admin, permissions: data.permissions })
      return data
    },
    // 刷新页面后用 token 换回身份与权限；失败即清会话跳登录
    async restore({ commit }) {
      try {
        if (!readToken()) {
          commit('clearSession')
          return false
        }
        const data = await fetchMe()
        commit('setSession', { token: '', admin: data.admin, permissions: data.permissions })
        return true
      } catch (error) {
        commit('clearSession')
        return false
      } finally {
        commit('setReady', true)
      }
    },
    logout({ commit }) {
      commit('clearSession')
    },
  },
})
