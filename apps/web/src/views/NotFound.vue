<template>
  <div class="not-found">
    <el-result
      icon="error"
      title="404"
      sub-title="Page not found"
    >
      <template #extra>
        <router-link to="/">
          <el-button type="primary">Back to Home</el-button>
        </router-link>
      </template>
    </el-result>
  </div>
</template>

<script setup lang="ts">
// No script needed for this simple component
</script>

<style scoped>
.not-found {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
}
</style>