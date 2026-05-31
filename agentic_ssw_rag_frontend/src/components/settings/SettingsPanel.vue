<script setup>
defineProps({
  accessTagsText: {
    type: String,
    default: '',
  },
  topK: {
    type: Number,
    default: 5,
  },
})

defineEmits(['update:accessTagsText', 'update:topK', 'persist'])
</script>

<template>
  <section class="panel settings-panel">
    <label>
      <span>访问标签</span>
      <input
        :value="accessTagsText"
        type="text"
        placeholder="finance, hr"
        @input="$emit('update:accessTagsText', $event.target.value)"
        @blur="$emit('persist')"
      />
    </label>
    <label>
      <span>Top K</span>
      <input
        :value="topK"
        type="number"
        min="1"
        max="100"
        @input="$emit('update:topK', Number($event.target.value || 5))"
        @blur="$emit('persist')"
      />
    </label>
  </section>
</template>
