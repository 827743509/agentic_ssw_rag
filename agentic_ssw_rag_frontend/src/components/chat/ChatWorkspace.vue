<script setup>
import { nextTick, ref, watch } from 'vue'
import MessageList from './MessageList.vue'
import QuestionComposer from './QuestionComposer.vue'

const props = defineProps({
  messages: {
    type: Array,
    default: () => [],
  },
  question: {
    type: String,
    default: '',
  },
  answering: {
    type: Boolean,
    default: false,
  },
  canSend: {
    type: Boolean,
    default: false,
  },
  statusMessage: {
    type: String,
    default: '',
  },
  statusError: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['update:question', 'clear', 'send'])
const chatBody = ref(null)

async function scrollToBottom() {
  await nextTick()
  if (chatBody.value) {
    chatBody.value.scrollTop = chatBody.value.scrollHeight
  }
}

watch(
  () => [props.messages.length, props.answering],
  () => {
    scrollToBottom()
  },
)
</script>

<template>
  <section class="chat-panel">
    <header class="chat-header">
      <div>
        <p>当前对话</p>
        <h2>知识库问答</h2>
      </div>
      <button class="secondary-button" type="button" @click="$emit('clear')">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M3 6h18" />
          <path d="M8 6V4h8v2" />
          <path d="M6 6l1 15h10l1-15" />
          <path d="M10 11v6" />
          <path d="M14 11v6" />
        </svg>
        <span>清空对话</span>
      </button>
    </header>

    <div ref="chatBody" class="chat-body">
      <MessageList :messages="messages" :answering="answering" />
    </div>

    <QuestionComposer
      :question="question"
      :can-send="canSend"
      :status-message="statusMessage"
      :status-error="statusError"
      @update:question="$emit('update:question', $event)"
      @send="$emit('send')"
    />
  </section>
</template>
