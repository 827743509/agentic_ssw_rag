<script setup>
import { formatSize, formatTime } from '../../utils/formatters'

const props = defineProps({
  documents: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  deletingId: {
    type: String,
    default: '',
  },
  downloadingId: {
    type: String,
    default: '',
  },
  deleteDocument: {
    type: Function,
    required: true,
  },
  downloadDocument: {
    type: Function,
    required: true,
  },
})

async function handleDelete(document) {
  if (props.deletingId) return
  const confirmed = window.confirm(`删除文件：${document.file_name}`)
  if (!confirmed) return
  await props.deleteDocument(document)
}

async function handleDownload(document) {
  if (props.downloadingId) return
  await props.downloadDocument(document)
}
</script>

<template>
  <section class="panel documents-panel">
    <div class="panel-title">
      <h2>文件管理</h2>
      <span>{{ documents.length }}</span>
    </div>
    <div v-if="loading" class="empty-state">加载中</div>
    <div v-else-if="!documents.length" class="empty-state">暂无文档</div>
    <ul v-else class="document-list">
      <li v-for="document in documents" :key="document.id">
        <div class="document-meta">
          <strong>{{ document.file_name }}</strong>
          <span>
            {{ formatSize(document.size) }} · {{ document.node_count }} chunks ·
            {{ formatTime(document.uploaded_at) }}
          </span>
        </div>
        <div class="document-actions">
          <button
            class="icon-button"
            type="button"
            title="下载文件"
            :disabled="downloadingId === document.id"
            @click="handleDownload(document)"
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 3v12" />
              <path d="m7 10 5 5 5-5" />
              <path d="M5 21h14" />
            </svg>
          </button>
          <button
            class="icon-button danger"
            type="button"
            title="删除文件"
            :disabled="deletingId === document.id"
            @click="handleDelete(document)"
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M3 6h18" />
              <path d="M8 6V4h8v2" />
              <path d="M6 6l1 15h10l1-15" />
              <path d="M10 11v6" />
              <path d="M14 11v6" />
            </svg>
          </button>
        </div>
      </li>
    </ul>
  </section>
</template>
