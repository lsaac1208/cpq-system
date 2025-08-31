# CPQ系统 API 文档 / CPQ System API Documentation

[中文](#api-文档) | [English](#api-documentation)

---

## API 文档

### 📡 基础信息

- **Base URL**: `http://localhost:5000/api/v1`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON
- **编码**: UTF-8

### 🔐 认证接口

#### 用户登录
```http
POST /auth/login
```

**请求体**:
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**响应**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1Q...",
  "refresh_token": "eyJ0eXAiOiJKV1Q...",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "email": "admin@example.com"
  }
}
```

#### 获取用户信息
```http
GET /auth/me
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "id": 1,
  "username": "admin",
  "role": "admin",
  "email": "admin@example.com"
}
```

#### 用户注册
```http
POST /auth/register
```

**请求体**:
```json
{
  "username": "newuser",
  "password": "password123",
  "email": "user@example.com",
  "role": "user"
}
```

### 📦 产品管理接口

#### 获取产品列表
```http
GET /products?page=1&per_page=20&search=keyword
```

**查询参数**:
- `page`: 页码 (默认: 1)
- `per_page`: 每页数量 (默认: 20)
- `search`: 搜索关键词 (可选)
- `category`: 产品分类 (可选)

**响应**:
```json
{
  "products": [
    {
      "id": 1,
      "code": "PROD-001",
      "name": "高端服务器",
      "category": "服务器",
      "base_price": 5000.00,
      "description": "企业级高性能服务器",
      "specifications": {
        "CPU": "Intel Xeon",
        "内存": "32GB DDR4",
        "存储": "1TB SSD"
      },
      "images": ["image1.jpg", "image2.jpg"],
      "created_at": "2025-08-31T05:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 4,
    "pages": 1
  }
}
```

#### 创建产品
```http
POST /products
Authorization: Bearer {access_token}
```

**请求体**:
```json
{
  "code": "PROD-002",
  "name": "新产品",
  "category": "分类",
  "base_price": 1000.00,
  "description": "产品描述",
  "specifications": {
    "规格1": "值1",
    "规格2": "值2"
  }
}
```

#### 更新产品
```http
PUT /products/{product_id}
Authorization: Bearer {access_token}
```

#### 删除产品
```http
DELETE /products/{product_id}
Authorization: Bearer {access_token}
```

### 💰 报价管理接口

#### 获取单产品报价列表
```http
GET /quotes?page=1&per_page=20&status=all&sort_by=created_at&sort_order=desc
```

**查询参数**:
- `page`: 页码
- `per_page`: 每页数量
- `status`: 状态过滤 (`draft`, `pending`, `approved`, `rejected`, `expired`, `all`)
- `customer_name`: 客户名称过滤
- `date_from`: 开始日期
- `date_to`: 结束日期
- `sort_by`: 排序字段
- `sort_order`: 排序方向

**响应**:
```json
{
  "quotes": [
    {
      "id": 1,
      "quote_number": "Q-20250831093530-0003",
      "customer_name": "Power Solutions Inc.",
      "customer_email": "orders@powersol.com",
      "customer_company": "Power Solutions Inc.",
      "status": "pending",
      "total_price": 899.00,
      "final_price": 899.00,
      "valid_until": "2025-09-30T00:00:00Z",
      "created_at": "2025-08-31T09:35:30Z",
      "product": {
        "id": 1,
        "name": "高端服务器",
        "code": "PROD-001"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 3,
    "pages": 1
  }
}
```

#### 获取多产品报价列表
```http
GET /multi-quotes?page=1&per_page=20
```

#### 创建单产品报价
```http
POST /quotes
Authorization: Bearer {access_token}
```

**请求体**:
```json
{
  "customer_name": "客户名称",
  "customer_email": "customer@example.com",
  "customer_company": "客户公司",
  "product_id": 1,
  "configuration": {
    "CPU": "升级版",
    "内存": "64GB"
  },
  "discount_percentage": 10,
  "tax_percentage": 8,
  "notes": "备注信息",
  "valid_until": "2025-12-31"
}
```

#### 创建多产品报价
```http
POST /multi-quotes
Authorization: Bearer {access_token}
```

**请求体**:
```json
{
  "customer_name": "客户名称",
  "customer_email": "customer@example.com",
  "items": [
    {
      "product_id": 1,
      "quantity": 2,
      "unit_price": 5000.00,
      "configuration": {
        "规格": "高配"
      }
    },
    {
      "product_id": 2,
      "quantity": 1,
      "unit_price": 2000.00
    }
  ],
  "discount_percentage": 5,
  "tax_percentage": 8,
  "notes": "多产品报价"
}
```

### 🤖 AI分析接口

#### 文档分析
```http
POST /ai-analysis/analyze
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

**请求**:
- `file`: 上传的文档文件
- `analysis_type`: 分析类型 (`full`, `basic`, `custom`)

**响应**:
```json
{
  "analysis_id": "uuid-string",
  "success": true,
  "extracted_data": {
    "basic_info": {
      "name": "产品名称",
      "category": "产品分类",
      "description": "产品描述"
    },
    "specifications": {
      "spec1": "value1",
      "spec2": "value2"
    },
    "pricing_info": {
      "base_price": 1000.00,
      "currency": "USD"
    }
  },
  "overall_confidence": 0.85,
  "processing_time": 2.5
}
```

#### 获取分析历史
```http
GET /ai-analysis/history?page=1&per_page=10
Authorization: Bearer {access_token}
```

#### 批量分析
```http
POST /batch-analysis/start
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

### 🔍 搜索接口

#### 产品搜索
```http
GET /search/products?q=关键词&category=分类&min_price=100&max_price=5000
```

#### 报价搜索
```http
GET /search/quotes?q=关键词&status=pending&customer=客户名
```

### 📊 统计接口

#### 仪表盘数据
```http
GET /dashboard/stats
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "products_count": 4,
  "quotes_count": 4,
  "pending_quotes": 1,
  "total_revenue": 1899.00,
  "recent_quotes": [...],
  "recent_analysis": [...]
}
```

### ⚙️ 系统接口

#### 健康检查
```http
GET /health
```

**响应**:
```json
{
  "status": "healthy",
  "database": "connected",
  "ai_service": "available",
  "version": "1.2.0",
  "uptime": "2h 30m"
}
```

#### 性能监控
```http
GET /monitoring/performance
Authorization: Bearer {access_token}
```

---

## API Documentation (English)

### 📡 Base Information

- **Base URL**: `http://localhost:5000/api/v1`
- **Authentication**: JWT Bearer Token
- **Data Format**: JSON
- **Encoding**: UTF-8

### 🔐 Authentication Endpoints

#### User Login
```http
POST /auth/login
```

**Request Body**:
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1Q...",
  "refresh_token": "eyJ0eXAiOiJKV1Q...",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "email": "admin@example.com"
  }
}
```

### 📦 Product Management

#### Get Products
```http
GET /products?page=1&per_page=20&search=keyword
```

### 💰 Quote Management

#### Get Single Product Quotes
```http
GET /quotes?page=1&per_page=20&status=all
```

#### Get Multi Product Quotes
```http
GET /multi-quotes?page=1&per_page=20
```

### 🤖 AI Analysis

#### Document Analysis
```http
POST /ai-analysis/analyze
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

### 🔍 Search

#### Product Search
```http
GET /search/products?q=keyword&category=category
```

### 📊 Analytics

#### Dashboard Statistics
```http
GET /dashboard/stats
Authorization: Bearer {access_token}
```

### ⚙️ System

#### Health Check
```http
GET /health
```

---

## 🔧 错误代码 / Error Codes

| 状态码 | 错误类型 | 说明 |
|--------|----------|------|
| 200 | 成功 | 请求成功 |
| 400 | 请求错误 | 请求参数错误 |
| 401 | 未授权 | 需要登录认证 |
| 403 | 禁止访问 | 权限不足 |
| 404 | 未找到 | 资源不存在 |
| 422 | 验证错误 | 数据验证失败 |
| 500 | 服务器错误 | 内部服务器错误 |

## 📝 使用示例 / Usage Examples

### JavaScript/Axios 示例
```javascript
// 登录
const loginResponse = await axios.post('/api/v1/auth/login', {
  username: 'admin',
  password: 'admin123'
});

const token = loginResponse.data.access_token;

// 获取产品列表
const productsResponse = await axios.get('/api/v1/products', {
  headers: {
    'Authorization': `Bearer ${token}`
  },
  params: {
    page: 1,
    per_page: 20
  }
});

// 创建报价
const quoteResponse = await axios.post('/api/v1/quotes', {
  customer_name: '测试客户',
  customer_email: 'test@example.com',
  product_id: 1,
  discount_percentage: 10
}, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

### Python/Requests 示例
```python
import requests

# 登录
login_response = requests.post('http://localhost:5000/api/v1/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})

token = login_response.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# 获取产品列表
products = requests.get('http://localhost:5000/api/v1/products', 
                       headers=headers,
                       params={'page': 1, 'per_page': 20})

# 创建报价
quote = requests.post('http://localhost:5000/api/v1/quotes',
                     headers=headers,
                     json={
                         'customer_name': '测试客户',
                         'customer_email': 'test@example.com',
                         'product_id': 1,
                         'discount_percentage': 10
                     })
```

### cURL 示例
```bash
# 登录
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 获取产品列表 (需要替换TOKEN)
curl -X GET http://localhost:5000/api/v1/products \
  -H "Authorization: Bearer TOKEN" \
  -G -d "page=1" -d "per_page=20"

# 创建报价 (需要替换TOKEN)
curl -X POST http://localhost:5000/api/v1/quotes \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "测试客户",
    "customer_email": "test@example.com",
    "product_id": 1,
    "discount_percentage": 10
  }'
```

---

## API Documentation (English)

### 📡 Base Information

- **Base URL**: `http://localhost:5000/api/v1`
- **Authentication**: JWT Bearer Token
- **Data Format**: JSON
- **Encoding**: UTF-8

### 🔐 Authentication Endpoints

#### User Login
```http
POST /auth/login
```

#### Get User Info
```http
GET /auth/me
Authorization: Bearer {access_token}
```

#### User Registration
```http
POST /auth/register
```

### 📦 Product Management

#### Get Products List
```http
GET /products?page=1&per_page=20&search=keyword
```

#### Create Product
```http
POST /products
Authorization: Bearer {access_token}
```

#### Update Product
```http
PUT /products/{product_id}
Authorization: Bearer {access_token}
```

#### Delete Product
```http
DELETE /products/{product_id}
Authorization: Bearer {access_token}
```

### 💰 Quote Management

#### Get Single Product Quotes
```http
GET /quotes?page=1&per_page=20&status=all
```

#### Get Multi Product Quotes
```http
GET /multi-quotes?page=1&per_page=20
```

#### Create Single Product Quote
```http
POST /quotes
Authorization: Bearer {access_token}
```

#### Create Multi Product Quote
```http
POST /multi-quotes
Authorization: Bearer {access_token}
```

### 🤖 AI Analysis

#### Document Analysis
```http
POST /ai-analysis/analyze
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

#### Get Analysis History
```http
GET /ai-analysis/history?page=1&per_page=10
Authorization: Bearer {access_token}
```

#### Start Batch Analysis
```http
POST /batch-analysis/start
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

### 🔍 Search

#### Product Search
```http
GET /search/products?q=keyword&category=category&min_price=100&max_price=5000
```

#### Quote Search
```http
GET /search/quotes?q=keyword&status=pending&customer=customer_name
```

### 📊 Analytics

#### Dashboard Statistics
```http
GET /dashboard/stats
Authorization: Bearer {access_token}
```

### ⚙️ System

#### Health Check
```http
GET /health
```

#### Performance Monitoring
```http
GET /monitoring/performance
Authorization: Bearer {access_token}
```

---

## 🛡️ 安全说明 / Security Notes

### 认证与授权
- 所有API接口（除了登录和健康检查）都需要JWT认证
- Token有效期为24小时
- 支持Token刷新机制
- 基于角色的权限控制

### 数据安全
- 所有敏感数据传输使用HTTPS
- 密码使用bcrypt加密存储
- SQL注入防护
- XSS攻击防护

### 限流与监控
- API请求频率限制
- 系统性能实时监控
- 异常请求检测与报警

---

## 📞 技术支持 / Technical Support

如有API使用问题，请联系：
- **GitHub Issues**: https://github.com/lsaac1208/cpq-system/issues
- **技术文档**: 查看项目docs目录
- **示例代码**: 参考tests目录中的测试用例

For API usage questions, please contact:
- **GitHub Issues**: https://github.com/lsaac1208/cpq-system/issues
- **Documentation**: Check the docs directory
- **Example Code**: Refer to test cases in tests directory