# 珍果链 - 水果批发小程序

<div align="center">

一个基于 uni-app + FastAPI 的水果批发报价与预订小程序

[![Vue 3](https://img.shields.io/badge/Vue-3.x-brightgreen.svg)](https://vuejs.org/)
[![uni-app](https://img.shields.io/badge/uni--app-Vue3-blue.svg)](https://uniapp.dcloud.net.cn/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)

</div>

---

## 项目简介

**珍果链**是一款面向水果批发行业的小程序解决方案，为供应商和采购客户提供便捷的报价、预订、管理平台。

### 主要功能

#### 客户端功能
- 🏠 **首页** - 查看最新水果报价，支持分类筛选和关键词搜索
- 📂 **分类浏览** - 按水果类别查看商品
- 🛒 **购物车** - 添加商品至购物车，批量下单
- 👤 **个人中心** - 管理个人信息、收货地址、订单记录
- 📝 **订单管理** - 查看订单详情、订单状态跟踪
- ✅ **客户认证** - 提交认证资料，获取批发资质

#### 供应商管理后台
- 🔐 **管理员登录** - 安全的后台登录机制
- 📊 **销售统计** - 查看销售数据、订单统计
- 📦 **订单管理** - 处理客户订单，更新订单状态
- 🍎 **报价管理** - 发布、编辑水果报价信息
- 👥 **用户管理** - 管理客户信息
- ✔️ **认证审核** - 审核客户提交的认证申请

---

## 技术栈

### 前端
- **框架**: uni-app (Vue 3)
- **语言**: JavaScript
- **UI**: 原生小程序组件
- **状态管理**: Vue 3 Composition API

### 后端
- **框架**: FastAPI
- **数据库**: MySQL (通过 SQLAlchemy ORM)
- **认证**: JWT (python-jose)
- **密码加密**: bcrypt
- **数据库迁移**: Alembic

---

## 项目结构

```
.
├── pages/                  # 小程序页面
│   ├── index/             # 首页 - 水果报价列表
│   ├── category/          # 分类页面
│   ├── cart/              # 购物车
│   ├── mine/              # 个人中心
│   ├── address/           # 地址管理
│   ├── profile/           # 个人信息
│   ├── product/           # 商品详情
│   ├── order/             # 订单相关
│   │   ├── create/        # 创建订单
│   │   └── list/          # 订单列表
│   ├── verify/            # 客户认证
│   ├── agreement/         # 用户协议
│   └── admin/             # 管理后台
│       ├── login/         # 管理员登录
│       ├── orders/        # 订单管理
│       ├── stats/         # 销售统计
│       ├── fruits/        # 报价管理
│       ├── users/         # 用户管理
│       └── verifications/ # 认证审核
├── composables/           # Vue 组合式函数
│   └── useFruitQuotes.js  # 水果报价数据逻辑
├── utils/                 # 工具函数
│   ├── request.js         # API 请求封装
│   ├── auth.js            # 客户认证逻辑
│   ├── admin.js           # 管理员认证逻辑
│   ├── cart.js            # 购物车逻辑
│   ├── format.js          # 格式化工具
│   ├── share.js           # 分享功能
│   └── categoryIcons.js   # 分类图标配置
├── static/                # 静态资源
│   └── tabbar/            # 底部导航图标
├── backend/               # 后端服务
│   ├── app/
│   │   ├── api/           # API 路由
│   │   │   ├── public.py  # 公开接口
│   │   │   ├── auth.py    # 认证接口
│   │   │   └── admin.py   # 管理接口
│   │   ├── models/        # 数据模型
│   │   ├── schemas/       # Pydantic 模式
│   │   ├── services/      # 业务逻辑
│   │   ├── core/          # 核心配置
│   │   └── db/            # 数据库初始化
│   ├── migrations/        # 数据库迁移
│   └── uploads/           # 上传文件存储
├── App.vue                # 应用入口
├── main.js                # 主入口文件
├── pages.json             # 页面配置
├── manifest.json          # 应用配置
└── uni.scss               # 全局样式变量
```

---

## 快速开始

### 前端开发

#### 环境要求
- Node.js 16+
- HBuilderX 或 VS Code (推荐使用 HBuilderX 进行小程序开发)

#### 安装与运行

1. 克隆项目
```bash
git clone <repository-url>
cd my-home
```

2. 使用 HBuilderX 打开项目

3. 运行到微信小程序
   - 点击 `运行` -> `运行到小程序模拟器` -> `微信开发者工具`

4. 或者使用 CLI 方式（需安装 @dcloudio/uni-cli）
```bash
npm install -g @dcloudio/uni-cli
npm install
npm run dev:mp-weixin
```

### 后端部署

#### 环境要求
- Python 3.8+
- MySQL 5.7+

#### 安装步骤

1. 进入后端目录
```bash
cd backend
```

2. 创建虚拟环境
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等参数
```

5. 创建数据库
```sql
CREATE DATABASE fruit_quote CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

6. 初始化数据库
```bash
python -m app.db.init_db
```

7. 启动服务
```bash
uvicorn app.main:app --reload
```

8. 访问 API 文档
```
http://127.0.0.1:8000/docs
```

#### 默认管理员账号
- 用户名: `admin`
- 密码: `admin123456`

> ⚠️ **重要**: 生产环境请务必修改默认密码

---

## API 接口

### 公开接口
- `GET /categories` - 获取水果分类列表
- `GET /fruits` - 获取水果报价列表
- `GET /fruits/{id}` - 获取水果详情

### 认证接口
- `POST /customers/login` - 客户登录
- `POST /customers/register` - 客户注册
- `POST /admin/login` - 管理员登录

### 客户接口
- `GET /customers/me` - 获取当前用户信息
- `PUT /customers/me` - 更新用户信息
- `POST /customers/avatar` - 上传头像
- `POST /customers/verification` - 提交认证
- `GET /customers/addresses` - 获取地址列表
- `POST /customers/addresses` - 创建地址
- `GET /orders` - 获取订单列表
- `POST /orders` - 创建订单

### 管理接口
- `GET /admin/stats` - 销售统计
- `GET /admin/orders` - 订单管理
- `PUT /admin/orders/{id}` - 更新订单
- `GET /admin/fruits` - 水果列表
- `POST /admin/fruits` - 创建水果
- `PUT /admin/fruits/{id}` - 更新水果
- `GET /admin/users` - 用户列表
- `GET /admin/verifications` - 认证列表
- `PUT /admin/verifications/{id}` - 审核认证

---

## 配置说明

### 小程序配置

在 `manifest.json` 中配置小程序 AppID：
```json
{
  "mp-weixin": {
    "appid": "your-app-id"
  }
}
```

### API 地址配置

在 `utils/request.js` 中修改 API 基础地址：
```javascript
export const API_BASE_URL = 'https://your-api-domain.com/api'
```

### 后端配置

在 `backend/.env` 中配置：
```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/fruit_quote
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

---

## 开发指南

### 代码规范
- 前端使用 Vue 3 Composition API
- 使用 async/await 处理异步操作
- 统一的错误处理机制
- 图片上传前自动压缩

### 分支管理
- `master` - 主分支，生产环境代码
- 开发新功能请创建 feature 分支

### 提交规范
```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式调整
refactor: 重构
test: 测试相关
chore: 构建/工具变动
```

---

## 部署说明

### 小程序发布
1. 在 HBuilderX 中点击 `发行` -> `小程序-微信`
2. 上传代码至微信后台
3. 在微信公众平台提交审核

### 后端部署
推荐使用 Docker 或直接部署到云服务器：
```bash
# 使用 gunicorn + uvicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

## 许可证

本项目仅供学习和参考使用。

---

## 联系方式

如有问题或建议，欢迎提交 Issue。

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给一个 Star ⭐**

</div>
