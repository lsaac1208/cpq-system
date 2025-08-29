// Element Plus 消息通知工具
import { ElMessage } from 'element-plus'

// 封装 ElMessage 方法来解决类型问题
export const showMessage = {
  success: (message: string) => {
    ElMessage({
      message,
      type: 'success'
    })
  },
  
  error: (message: string) => {
    ElMessage({
      message,
      type: 'error'
    })
  },
  
  warning: (message: string) => {
    ElMessage({
      message,
      type: 'warning'
    })
  },
  
  info: (message: string) => {
    ElMessage({
      message,
      type: 'info'
    })
  }
}

export default showMessage