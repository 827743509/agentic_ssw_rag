import { ref } from 'vue'

const STORAGE_KEYS = {
  accessTags: 'rag.accessTags',
  topK: 'rag.topK',
}

export function useRagSettings() {
  const accessTagsText = ref(localStorage.getItem(STORAGE_KEYS.accessTags) || '')
  const topK = ref(Number(localStorage.getItem(STORAGE_KEYS.topK) || 20))

  function persistSettings() {
    localStorage.setItem(STORAGE_KEYS.accessTags, accessTagsText.value.trim())
    localStorage.setItem(STORAGE_KEYS.topK, String(topK.value || 20))
  }

  function parseAccessTags() {
    return accessTagsText.value
      .split(/[\s,，]+/)
      .map((tag) => tag.trim())
      .filter(Boolean)
  }

  return {
    accessTagsText,
    topK,
    persistSettings,
    parseAccessTags,
  }
}
