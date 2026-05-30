<script setup>
defineProps({
  question: {
    type: String,
    default: '',
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

const emit = defineEmits(['update:question', 'send'])

function handleKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    emit('send')
  }
}
</script>

<template>
  <footer class="composer">
    <div v-if="statusMessage" class="status-line" :class="{ error: statusError }">
      {{ statusMessage }}
    </div>
    <div class="composer-box">
      <textarea
        :value="question"
        rows="1"
        placeholder="输入问题"
        @input="$emit('update:question', $event.target.value)"
        @keydown="handleKeydown"
      ></textarea>
      <button class="send-button" type="button" title="发送" :disabled="!canSend" @click="$emit('send')">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M22 2 11 13" />
          <path d="m22 2-7 20-4-9-9-4 20-7z" />
        </svg>
      </button>
    </div>
  </footer>
</template>
