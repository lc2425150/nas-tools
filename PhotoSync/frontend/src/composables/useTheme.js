import { ref, watch } from 'vue'
const isDark = ref(localStorage.getItem('theme')==='dark'||(!localStorage.getItem('theme')&&window.matchMedia('(prefers-color-scheme:dark)').matches))
watch(isDark, v => { document.documentElement.classList.toggle('dark',v); localStorage.setItem('theme',v?'dark':'light') })
export function useTheme() { return { isDark, toggle:()=>{isDark.value=!isDark.value} } }
