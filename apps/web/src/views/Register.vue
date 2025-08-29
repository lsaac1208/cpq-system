<template>
  <div class="register-container">
    <div class="register-card">
      <div class="register-header">
        <h2>Create Account</h2>
        <p>Join CPQ System</p>
      </div>

      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        @submit.prevent="handleRegister"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item prop="first_name">
              <el-input
                v-model="registerForm.first_name"
                placeholder="First Name"
                size="large"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item prop="last_name">
              <el-input
                v-model="registerForm.last_name"
                placeholder="Last Name"
                size="large"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item prop="username">
          <el-input
            v-model="registerForm.username"
            placeholder="Username"
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="email">
          <el-input
            v-model="registerForm.email"
            placeholder="Email"
            size="large"
            :prefix-icon="Message"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="Password"
            size="large"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item prop="confirmPassword">
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="Confirm Password"
            size="large"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handleRegister"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            style="width: 100%"
            :loading="authStore.loading"
            @click="handleRegister"
          >
            Create Account
          </el-button>
        </el-form-item>
      </el-form>

      <div class="register-footer">
        <p>
          Already have an account? 
          <router-link to="/login" class="link">Login here</router-link>
        </p>
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
import { User, Lock, Message } from '@element-plus/icons-vue'
import type { RegisterRequest } from '@/types/auth'

const router = useRouter()
const authStore = useAuthStore()

const registerFormRef = ref<InstanceType<typeof ElForm>>()

const registerForm = reactive<RegisterRequest & { confirmPassword: string }>({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  first_name: '',
  last_name: ''
})

const validateConfirmPassword = (rule: any, value: string, callback: Function) => {
  if (value !== registerForm.password) {
    callback(new Error('Passwords do not match'))
  } else {
    callback()
  }
}

const registerRules = {
  first_name: [
    { required: true, message: 'Please enter first name', trigger: 'blur' }
  ],
  last_name: [
    { required: true, message: 'Please enter last name', trigger: 'blur' }
  ],
  username: [
    { required: true, message: 'Please enter username', trigger: 'blur' },
    { min: 3, message: 'Username must be at least 3 characters', trigger: 'blur' }
  ],
  email: [
    { required: true, message: 'Please enter email', trigger: 'blur' },
    { type: 'email', message: 'Please enter a valid email', trigger: 'blur' }
  ],
  password: [
    { required: true, message: 'Please enter password', trigger: 'blur' },
    { min: 6, message: 'Password must be at least 6 characters', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: 'Please confirm password', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const handleRegister = async () => {
  if (!registerFormRef.value) return

  try {
    await registerFormRef.value.validate()
    
    const { confirmPassword, ...userData } = registerForm
    const response = await authStore.register(userData)
    
    showMessage.success(response.message || 'Registration successful')
    router.push('/')
  } catch (error: any) {
    console.error('Registration failed:', error)
    showMessage.error(error.response?.data?.error || 'Registration failed')
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.register-card {
  background: white;
  border-radius: 10px;
  padding: 40px;
  width: 500px;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
}

.register-header {
  text-align: center;
  margin-bottom: 30px;
}

.register-header h2 {
  color: #409eff;
  margin: 0 0 10px 0;
  font-size: 28px;
  font-weight: 600;
}

.register-header p {
  color: #666;
  margin: 0;
  font-size: 14px;
}

.register-footer {
  text-align: center;
  margin-top: 20px;
}

.register-footer p {
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
</style>