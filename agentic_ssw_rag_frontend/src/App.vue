<script setup>
import { computed, onMounted } from 'vue'
import ChatWorkspace from './components/chat/ChatWorkspace.vue'
import DocumentManager from './components/documents/DocumentManager.vue'
import SettingsPanel from './components/settings/SettingsPanel.vue'
import { useChat } from './composables/useChat'
import { useDocuments } from './composables/useDocuments'
import { useRagSettings } from './composables/useRagSettings'

const { accessTagsText, topK, persistSettings, parseAccessTags } = useRagSettings()

const {
  documents: documentList,
  loadingDocuments,
  uploading,
  deletingId,
  downloadingId,
  notice,
  error: documentError,
  refreshDocuments,
  uploadFile,
  deleteStoredDocument,
  downloadStoredDocument,
} = useDocuments()

const {
  messages,
  question,
  answering,
  canSend,
  sendQuestion,
  clearMessages,
} = useChat({
  topK,
  persistSettings,
  parseAccessTags,
})

const statusMessage = computed(() => documentError.value || notice.value)
const hasStatusError = computed(() => Boolean(documentError.value))

onMounted(() => {
  persistSettings()
  refreshDocuments()
})
</script>

<template>
  <main class="app-shell">
    <aside class="sidebar">
      <section class="brand">
        <div>
          <p>Agentic RAG</p>
          <h1>知识库工作台</h1>
        </div>
        <button class="icon-button" type="button" title="刷新文档" @click="refreshDocuments">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M20 12a8 8 0 1 1-2.34-5.66" />
            <path d="M20 4v6h-6" />
          </svg>
        </button>
      </section>

      <DocumentManager
        :documents="documentList"
        :loading="loadingDocuments"
        :uploading="uploading"
        :deleting-id="deletingId"
        :downloading-id="downloadingId"
        :upload-file="uploadFile"
        :delete-document="deleteStoredDocument"
        :download-document="downloadStoredDocument"
      />

      <SettingsPanel
        v-model:access-tags-text="accessTagsText"
        v-model:top-k="topK"
        @persist="persistSettings"
      />
    </aside>

    <ChatWorkspace
      v-model:question="question"
      :messages="messages"
      :answering="answering"
      :can-send="canSend"
      :status-message="statusMessage"
      :status-error="hasStatusError"
      @clear="clearMessages"
      @send="sendQuestion"
    />
  </main>
</template>
