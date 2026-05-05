<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { chatWithAgent, deleteDocument, downloadDocument, listDocuments, uploadDocument } from './api'
import animeLibraryAssistant from './assets/anime-library-assistant.png'

const supportedTypes = '.txt,.md,.pdf,.docx,.pptx,.csv,.xlsx'

const documents = ref([])
const currentFile = ref(null)
const fileInput = ref(null)
const messages = ref([])
const question = ref('')
const chatBody = ref(null)
const apiKey = ref(localStorage.getItem('rag.apiKey') || '')
const accessTagsText = ref(localStorage.getItem('rag.accessTags') || '')
const topK = ref(Number(localStorage.getItem('rag.topK') || 20))
const sessionId = ref(localStorage.getItem('rag.sessionId') || crypto.randomUUID())
const loadingDocuments = ref(false)
const uploading = ref(false)
const deletingId = ref('')
const downloadingId = ref('')
const answering = ref(false)
const notice = ref('')
const error = ref('')

const canSend = computed(() => question.value.trim() && !answering.value)
const currentFileName = computed(() => currentFile.value?.name || '选择文件')

function persistSettings() {
  localStorage.setItem('rag.apiKey', apiKey.value.trim())
  localStorage.setItem('rag.accessTags', accessTagsText.value.trim())
  localStorage.setItem('rag.topK', String(topK.value || 20))
  localStorage.setItem('rag.sessionId', sessionId.value)
}

function parseAccessTags() {
  return accessTagsText.value
    .split(/[\s,，]+/)
    .map((tag) => tag.trim())
    .filter(Boolean)
}

function formatSize(size) {
  if (!Number.isFinite(size)) return '-'
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

function formatTime(value) {
  if (!value) return '-'
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function setFile(event) {
  currentFile.value = event.target.files?.[0] || null
}

function setDroppedFile(event) {
  currentFile.value = event.dataTransfer.files?.[0] || null
}

async function refreshDocuments() {
  loadingDocuments.value = true
  error.value = ''
  try {
    const data = await listDocuments(apiKey.value.trim())
    documents.value = data.documents || []
  } catch (err) {
    error.value = err.message
  } finally {
    loadingDocuments.value = false
  }
}

async function handleUpload() {
  if (!currentFile.value || uploading.value) return
  uploading.value = true
  error.value = ''
  notice.value = ''
  try {
    await uploadDocument(currentFile.value, apiKey.value.trim())
    notice.value = '文档已入库'
    currentFile.value = null
    if (fileInput.value) fileInput.value.value = ''
    await refreshDocuments()
  } catch (err) {
    error.value = err.message
  } finally {
    uploading.value = false
  }
}

async function handleDelete(document) {
  if (deletingId.value) return
  const confirmed = window.confirm(`删除文件：${document.file_name}`)
  if (!confirmed) return

  deletingId.value = document.id
  error.value = ''
  notice.value = ''
  try {
    await deleteDocument(document.id, apiKey.value.trim())
    notice.value = '文件已删除'
    await refreshDocuments()
  } catch (err) {
    error.value = err.message
  } finally {
    deletingId.value = ''
  }
}

async function handleDownload(document) {
  if (downloadingId.value) return

  downloadingId.value = document.id
  error.value = ''
  notice.value = ''
  try {
    await downloadDocument(document.id, apiKey.value.trim(), document.file_name)
    notice.value = '文件下载已开始'
  } catch (err) {
    error.value = err.message
  } finally {
    downloadingId.value = ''
  }
}

function newSession() {
  sessionId.value = crypto.randomUUID()
  messages.value = []
  persistSettings()
}

async function scrollToBottom() {
  await nextTick()
  if (chatBody.value) {
    chatBody.value.scrollTop = chatBody.value.scrollHeight
  }
}

async function sendQuestion() {
  const text = question.value.trim()
  if (!text || answering.value) return

  persistSettings()
  messages.value.push({ role: 'user', content: text })
  question.value = ''
  answering.value = true
  error.value = ''
  await scrollToBottom()

  try {
    const data = await chatWithAgent(
      {
        question: text,
        session_id: sessionId.value,
        access_tags: parseAccessTags(),
        top_k: topK.value ? Number(topK.value) : null,
      },
      apiKey.value.trim(),
    )
    messages.value.push({
      role: 'assistant',
      content: data.answer || '未返回回答',
      sources: data.sources || [],
    })
  } catch (err) {
    messages.value.push({
      role: 'error',
      content: err.message,
    })
  } finally {
    answering.value = false
    await scrollToBottom()
  }
}

function handleQuestionKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendQuestion()
  }
}

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
        <button class="primary-button" type="button" :disabled="!currentFile || uploading" @click="handleUpload">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 3v12" />
            <path d="m7 8 5-5 5 5" />
            <path d="M5 21h14" />
          </svg>
          <span>{{ uploading ? '入库中' : '上传入库' }}</span>
        </button>
      </section>

      <section class="panel settings-panel">
        <label>
          <span>API Key</span>
          <input v-model="apiKey" type="password" placeholder="dev-secret" @blur="persistSettings" />
        </label>
        <label>
          <span>访问标签</span>
          <input v-model="accessTagsText" type="text" placeholder="finance, hr" @blur="persistSettings" />
        </label>
        <label>
          <span>Top K</span>
          <input v-model.number="topK" type="number" min="1" max="100" @blur="persistSettings" />
        </label>
      </section>

      <section class="panel documents-panel">
        <div class="panel-title">
          <h2>文件管理</h2>
          <span>{{ documents.length }}</span>
        </div>
        <div v-if="loadingDocuments" class="empty-state">加载中</div>
        <div v-else-if="!documents.length" class="empty-state">暂无文档</div>
        <ul v-else class="document-list">
          <li v-for="document in documents" :key="document.id">
            <div class="document-meta">
              <strong>{{ document.file_name }}</strong>
              <span>{{ formatSize(document.size) }} · {{ document.node_count }} chunks · {{ formatTime(document.uploaded_at) }}</span>
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
    </aside>

    <section class="chat-panel">
      <header class="chat-header">
        <div>
          <p>当前会话</p>
          <h2>{{ sessionId.slice(0, 8) }}</h2>
        </div>
        <button class="secondary-button" type="button" @click="newSession">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 5v14" />
            <path d="M5 12h14" />
          </svg>
          <span>新会话</span>
        </button>
      </header>

      <div ref="chatBody" class="chat-body">
        <div v-if="!messages.length" class="welcome">
          <img class="welcome-art" :src="animeLibraryAssistant" alt="" />
          <h2>开始提问</h2>
          <p>暂无消息</p>
        </div>
        <article
          v-for="(message, index) in messages"
          :key="index"
          class="message"
          :class="`message-${message.role}`"
        >
          <span>{{ message.role === 'user' ? '你' : message.role === 'error' ? '错误' : '助手' }}</span>
          <p>{{ message.content }}</p>
          <div v-if="message.sources?.length" class="sources">
            <strong>来源</strong>
            <div v-for="(source, sourceIndex) in message.sources" :key="sourceIndex">
              {{ source.metadata?.file_name || source.metadata?.source_path || `片段 ${sourceIndex + 1}` }}
            </div>
          </div>
        </article>
        <article v-if="answering" class="message message-assistant pending">
          <span>助手</span>
          <p>生成中</p>
        </article>
      </div>

      <footer class="composer">
        <div v-if="notice || error" class="status-line" :class="{ error: !!error }">
          {{ error || notice }}
        </div>
        <div class="composer-box">
          <textarea
            v-model="question"
            rows="1"
            placeholder="输入问题"
            @keydown="handleQuestionKeydown"
          ></textarea>
          <button class="send-button" type="button" title="发送" :disabled="!canSend" @click="sendQuestion">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M22 2 11 13" />
              <path d="m22 2-7 20-4-9-9-4 20-7z" />
            </svg>
          </button>
        </div>
      </footer>
    </section>
  </main>
</template>
