<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h2>CPQ系统</h2>
        <p>电力设备制造商配置定价报价系统</p>
      </div>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="用户名"
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            size="large"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            style="width: 100%"
            :loading="authStore.loading"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <p>
          还没有账户？ 
          <router-link to="/register" class="link">立即注册</router-link>
        </p>
      </div>

      <!-- Demo Credentials -->
      <div class="demo-info">
        <h4>演示账户</h4>
        <p><strong>管理员:</strong> admin / password123</p>
        <p><strong>销售员:</strong> sales / password123</p>
        <p><strong>工程师:</strong> engineer / password123</p>
        <p><strong>经理:</strong> manager / password123</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElForm } from 'element-plus'
import { showMessage } from '@/utils/message'
import { User, Lock } from '@element-plus/icons-vue'
import type { LoginRequest } from '@/types/auth'

const router = useRouter()
const authStore = useAuthStore()

const loginFormRef = ref<InstanceType<typeof ElForm>>()

const loginForm = reactive<LoginRequest>({
  username: '',
  password: ''
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少需要6个字符', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return

  try {
    await loginFormRef.value.validate()
    
    const response = await authStore.login(loginForm)
    
    showMessage.success(response.data.message || '登录成功')
    router.push('/')
  } catch (error: any) {
    console.error('Login failed:', error)
    showMessage.error(error.response?.data?.error || '登录失败')
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  background: white;
  border-radius: 10px;
  padding: 40px;
  width: 400px;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h2 {
  color: #409eff;
  margin: 0 0 10px 0;
  font-size: 28px;
  font-weight: 600;
}

.login-header p {
  color: #666;
  margin: 0;
  font-size: 14px;
}

.login-footer {
  text-align: center;
  margin-top: 20px;
}

.login-footer p {
  color: #666;
  font-size: 14px;
  margin: 0;
}

.link {
  color: #409eff;
  text-decoration: none;
}

.link:hover {
  text-decoration: underline;
}

.demo-info {
  margin-top: 30px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 5px;
  border-left: 4px solid #409eff;
}

.demo-info h4 {
  margin: 0 0 10px 0;
  color: #409eff;
  font-size: 14px;
}

.demo-info p {
  margin: 5px 0;
  font-size: 12px;
  color: #666;
}
</style>