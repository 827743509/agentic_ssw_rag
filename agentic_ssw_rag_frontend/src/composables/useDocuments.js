import { ref } from 'vue'
import { deleteDocument, downloadDocument, listDocuments, uploadDocument } from '../api'

export function useDocuments() {
  const documents = ref([])
  const loadingDocuments = ref(false)
  const uploading = ref(false)
  const deletingId = ref('')
  const downloadingId = ref('')
  const notice = ref('')
  const error = ref('')

  function clearStatus() {
    notice.value = ''
    error.value = ''
  }

  async function refreshDocuments() {
    loadingDocuments.value = true
    error.value = ''
    try {
      const data = await listDocuments()
      documents.value = data?.documents || []
      return true
    } catch (err) {
      error.value = err.message
      return false
    } finally {
      loadingDocuments.value = false
    }
  }

  async function uploadFile(file) {
    if (!file || uploading.value) return false
    uploading.value = true
    clearStatus()
    try {
      await uploadDocument(file)
      notice.value = '文档已入库'
      await refreshDocuments()
      return true
    } catch (err) {
      error.value = err.message
      return false
    } finally {
      uploading.value = false
    }
  }

  async function deleteStoredDocument(document) {
    if (!document || deletingId.value) return false
    deletingId.value = document.id
    clearStatus()
    try {
      await deleteDocument(document.id)
      notice.value = '文档已删除'
      await refreshDocuments()
      return true
    } catch (err) {
      error.value = err.message
      return false
    } finally {
      deletingId.value = ''
    }
  }

  async function downloadStoredDocument(document) {
    if (!document || downloadingId.value) return false
    downloadingId.value = document.id
    clearStatus()
    try {
      await downloadDocument(document.id, document.file_name)
      notice.value = '文件下载已开始'
      return true
    } catch (err) {
      error.value = err.message
      return false
    } finally {
      downloadingId.value = ''
    }
  }

  return {
    documents,
    loadingDocuments,
    uploading,
    deletingId,
    downloadingId,
    notice,
    error,
    refreshDocuments,
    uploadFile,
    deleteStoredDocument,
    downloadStoredDocument,
  }
}
