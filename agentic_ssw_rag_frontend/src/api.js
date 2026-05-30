const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')

function buildUrl(path) {
  return `${API_BASE_URL}${path}`
}

async function parseResponse(response) {
  const text = await response.text()
  let data = null

  try {
    data = text ? JSON.parse(text) : null
  } catch {
    data = { detail: text }
  }

  if (!response.ok) {
    const detail = data?.detail
    if (Array.isArray(detail)) {
      throw new Error(detail.map((item) => item.msg).join('，') || '请求失败')
    }
    throw new Error(detail || data?.message || `请求失败：${response.status}`)
  }

  return data
}

export async function listDocuments() {
  const response = await fetch(buildUrl('/documents'))
  return parseResponse(response)
}

export async function uploadDocument(file) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(buildUrl('/documents/upload'), {
    method: 'POST',
    body: formData,
  })
  return parseResponse(response)
}

export async function deleteDocument(documentId) {
  const response = await fetch(buildUrl(`/documents/${documentId}`), {
    method: 'DELETE',
  })
  return parseResponse(response)
}

function getDownloadFileName(response, fallbackName) {
  const disposition = response.headers.get('content-disposition') || ''
  const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/i)
  if (utf8Match?.[1]) {
    return decodeURIComponent(utf8Match[1])
  }

  const asciiMatch = disposition.match(/filename="?([^"]+)"?/i)
  return asciiMatch?.[1] || fallbackName
}

export async function downloadDocument(documentId, fallbackName = 'download') {
  const response = await fetch(buildUrl(`/documents/${documentId}/download`))

  if (!response.ok) {
    return parseResponse(response)
  }

  const blob = await response.blob()
  const objectUrl = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = getDownloadFileName(response, fallbackName)
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(objectUrl)
  return true
}

export async function streamChatWithAgent(payload, onChunk) {
  const response = await fetch(buildUrl('/agent/chat'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    return parseResponse(response)
  }

  if (!response.body) {
    const text = await response.text()
    onChunk?.(text)
    return { answer: text }
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let answer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const chunk = decoder.decode(value, { stream: true })
    if (!chunk) continue

    answer += chunk
    onChunk?.(chunk, answer)
  }

  const tail = decoder.decode()
  if (tail) {
    answer += tail
    onChunk?.(tail, answer)
  }

  return { answer }
}
