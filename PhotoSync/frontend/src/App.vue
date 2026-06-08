<template>
  <div class="min-h-screen">
    <nav v-if="!isSetup" class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
      <div class="max-w-7xl mx-auto px-4 flex items-center justify-between h-14">
        <div class="flex items-center gap-6">
          <span class="text-lg font-bold text-blue-600">PhotoSync</span>
          <router-link v-for="item in nav" :key="item.path" :to="item.path"
            class="text-sm text-gray-600 dark:text-gray-400 hover:text-blue-600 transition-colors"
            :class="{'text-blue-600 font-medium':$route.path.startsWith(item.path)}">{{ item.label }}</router-link>
        </div>
        <ThemeToggle />
      </div>
    </nav>
    <main class="max-w-7xl mx-auto px-4 py-6"><router-view /></main>
  </div>
</template>
<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import ThemeToggle from './components/ThemeToggle.vue'
const router = useRouter()
const nav = [{path:'/',label:'仪表盘'},{path:'/profiles',label:'同步配置'},{path:'/history',label:'同步记录'},{path:'/gallery',label:'照片画廊'},{path:'/settings',label:'系统设置'}]
const isSetup = computed(() => router.currentRoute.value.path === '/setup')
</script>
