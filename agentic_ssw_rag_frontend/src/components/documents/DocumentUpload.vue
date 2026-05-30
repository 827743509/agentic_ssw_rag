<script setup>
import { computed, ref } from 'vue'

const supportedTypes = '.txt,.md,.pdf,.docx,.pptx,.csv,.xlsx'

const props = defineProps({
  uploading: {
    type: Boolean,
    default: false,
  },
  uploadFile: {
    type: Function,
    required: true,
  },
})

const fileInput = ref(null)
const currentFile = ref(null)
const currentFileName = computed(() => currentFile.value?.name || '选择文件')

function setFile(event) {
  currentFile.value = event.target.files?.[0] || null
}

function setDroppedFile(event) {
  currentFile.value = event.dataTransfer.files?.[0] || null
}

function resetFile() {
  currentFile.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

async function handleUpload() {
  if (!currentFile.value || props.uploading) return
  const uploaded = await props.uploadFile(currentFile.value)
  if (uploaded) {
    resetFile()
  }
}
</script>

<template>
  <section class="panel upload-panel">
    <div
      class="drop-zone"
      @dragover.prevent
      @drop.prevent="setDroppedFile"
      @click="fileInput?.click()"
    >
      <input
        ref="fileInput"
        class="file-input"
        type="file"
        :accept="supportedTypes"
        @change="setFile"
      />
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 15V3" />
        <path d="m7 8 5-5 5 5" />
        <path d="M5 15v4a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-4" />
      </svg>
      <span>{{ currentFileName }}</span>
    </div>
    <button
      class="primary-button"
      type="button"
      :disabled="!currentFile || uploading"
      @click="handleUpload"
    >
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 3v12" />
        <path d="m7 8 5-5 5 5" />
        <path d="M5 21h14" />
      </svg>
      <span>{{ uploading ? '入库中' : '上传入库' }}</span>
    </button>
  </section>
</template>
