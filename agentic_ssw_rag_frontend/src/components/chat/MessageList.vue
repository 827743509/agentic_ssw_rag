<script setup>
import animeLibraryAssistant from '../../assets/anime-library-assistant.png'

defineProps({
  messages: {
    type: Array,
    default: () => [],
  },
  answering: {
    type: Boolean,
    default: false,
  },
})

function roleLabel(role) {
  if (role === 'user') return '你'
  if (role === 'error') return '错误'
  return '助手'
}

function sourceLabel(source, index) {
  return source.metadata?.file_name || source.metadata?.source_path || `片段 ${index + 1}`
}
</script>

<template>
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
    <span>{{ roleLabel(message.role) }}</span>
    <p>{{ message.content }}</p>
    <div v-if="message.sources?.length" class="sources">
      <strong>来源</strong>
      <div v-for="(source, sourceIndex) in message.sources" :key="sourceIndex">
        {{ sourceLabel(source, sourceIndex) }}
      </div>
    </div>
  </article>

  <article v-if="answering && !messages.some((message) => message.role === 'assistant')" class="message message-assistant pending">
    <span>助手</span>
    <p>生成中</p>
  </article>
</template>
