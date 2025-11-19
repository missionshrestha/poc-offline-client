const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
}

async function request(path, { method = 'GET', headers = {}, body } = {}) {
  const url = path.startsWith('http') ? path : path

  const options = {
    method,
    headers: { ...DEFAULT_HEADERS, ...headers },
  }

  if (body !== undefined) {
    options.body = typeof body === 'string' ? body : JSON.stringify(body)
  }

  const response = await fetch(url, options)

  let data = null
  const text = await response.text()
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = text
    }
  }

  if (!response.ok) {
    const error = new Error(`HTTP ${response.status}`)
    error.status = response.status
    error.data = data
    throw error
  }

  return data
}

export function get(path) {
  return request(path, { method: 'GET' })
}

export function post(path, body, extraHeaders = {}) {
  return request(path, { method: 'POST', body, headers: extraHeaders })
}
