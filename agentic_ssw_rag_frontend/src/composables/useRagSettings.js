import { ref } from 'vue'

const STORAGE_KEYS = {
  accessTags: 'rag.accessTags',
  topK: 'rag.topK',
}

const DEFAULT_TOP_K = 5
const LEGACY_DEFAULT_TOP_K = '20'

function readTopK() {
  const storedTopK = localStorage.getItem(STORAGE_KEYS.topK)
  if (!storedTopK || storedTopK === LEGACY_DEFAULT_TOP_K) {
    return DEFAULT_TOP_K
  }

  const parsedTopK = Number(storedTopK)
  return Number.isFinite(parsedTopK) && parsedTopK > 0 ? parsedTopK : DEFAULT_TOP_K
}

export function useRagSettings() {
  const accessTagsText = ref(localStorage.getItem(STORAGE_KEYS.accessTags) || '')
  const topK = ref(readTopK())

  function persistSettings() {
    localStorage.setItem(STORAGE_KEYS.accessTags, accessTagsText.value.trim())
    localStorage.setItem(STORAGE_KEYS.topK, String(topK.value || DEFAULT_TOP_K))
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
