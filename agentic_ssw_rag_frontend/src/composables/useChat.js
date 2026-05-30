import { computed, ref } from 'vue'
import { streamChatWithAgent } from '../api'

export function useChat({ topK, persistSettings, parseAccessTags }) {
  const messages = ref([])
  const question = ref('')
  const answering = ref(false)
  const canSend = computed(() => Boolean(question.value.trim()) && !answering.value)

  async function sendQuestion() {
    const text = question.value.trim()
    if (!text || answering.value) return

    persistSettings()
    messages.value.push({ role: 'user', content: text })
    const assistantIndex = messages.value.push({ role: 'assistant', content: '', sources: [] }) - 1
    question.value = ''
    answering.value = true

    try {
      await streamChatWithAgent(
        {
          question: text,
          access_tags: parseAccessTags(),
          top_k: topK.value ? Number(topK.value) : null,
        },
        (chunk) => {
          messages.value[assistantIndex].content += chunk
        },
      )

      if (!messages.value[assistantIndex].content.trim()) {
        messages.value[assistantIndex].content = '未返回回答'
      }
    } catch (err) {
      messages.value.splice(assistantIndex, 1, {
        role: 'error',
        content: err.message,
      })
    } finally {
      answering.value = false
    }
  }

  function clearMessages() {
    messages.value = []
  }

  return {
    messages,
    question,
    answering,
    canSend,
    sendQuestion,
    clearMessages,
  }
}
