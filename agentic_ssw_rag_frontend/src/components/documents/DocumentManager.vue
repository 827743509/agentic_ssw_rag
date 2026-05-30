<script setup>
import DocumentList from './DocumentList.vue'
import DocumentUpload from './DocumentUpload.vue'

defineProps({
  documents: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  uploading: {
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
  uploadFile: {
    type: Function,
    required: true,
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
</script>

<template>
  <DocumentUpload :uploading="uploading" :upload-file="uploadFile" />
  <DocumentList
    :documents="documents"
    :loading="loading"
    :deleting-id="deletingId"
    :downloading-id="downloadingId"
    :delete-document="deleteDocument"
    :download-document="downloadDocument"
  />
</template>
