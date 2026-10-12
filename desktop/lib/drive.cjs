// Minimal Google Drive v3 client for the Colab handoff (drive.file scope: the app only sees
// files it created). The notebook updates the placeholder files the app creates, so the app
// can read the results back without a broader scope.
const fs = require('node:fs')
const path = require('node:path')

const API = 'https://www.googleapis.com/drive/v3'
const UPLOAD = 'https://www.googleapis.com/upload/drive/v3'
const FOLDER = 'application/vnd.google-apps.folder'
const ROOT_NAME = 'SpeakWise Desktop'
const HEARTBEAT_NAME = 'colab_heartbeat.json'

class DriveError extends Error {}

class Drive {
  constructor(auth, userDataDir) {
    this.auth = auth
    this.stateFile = path.join(userDataDir, 'drive-state.json')
  }

  async request(url, init = {}, timeoutMs = 30000) {
    const token = await this.auth.getAccessToken()
    const res = await fetch(url, {
      ...init,
      headers: { Authorization: `Bearer ${token}`, ...(init.headers || {}) },
      signal: AbortSignal.timeout(timeoutMs),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      const reason = body.error?.message || res.statusText
      throw new DriveError(`Google Drive request failed (${res.status}): ${reason}`)
    }
    return res
  }

  loadState() {
    try {
      return JSON.parse(fs.readFileSync(this.stateFile, 'utf8'))
    } catch {
      return {}
    }
  }

  saveState(state) {
    fs.writeFileSync(this.stateFile, JSON.stringify(state))
  }

  async exists(id) {
    if (!id) return false
    try {
      const res = await this.request(`${API}/files/${id}?fields=id,trashed`)
      return !(await res.json()).trashed
    } catch {
      return false
    }
  }

  async createJson(name, parent, obj) {
    const meta = { name, parents: [parent], mimeType: 'application/json' }
    const boundary = `sw${Date.now()}`
    const body =
      `--${boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n${JSON.stringify(meta)}\r\n` +
      `--${boundary}\r\nContent-Type: application/json\r\n\r\n${JSON.stringify(obj)}\r\n--${boundary}--`
    const res = await this.request(`${UPLOAD}/files?uploadType=multipart&fields=id`, {
      method: 'POST',
      headers: { 'Content-Type': `multipart/related; boundary=${boundary}` },
      body,
    })
    return (await res.json()).id
  }

  /** Root folder + heartbeat placeholder; recreated if the user deleted them. */
  async ensureWorkspace() {
    const state = this.loadState()
    if (!(await this.exists(state.rootId))) {
      const res = await this.request(`${API}/files?fields=id`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: ROOT_NAME, mimeType: FOLDER }),
      })
      state.rootId = (await res.json()).id
      state.heartbeatId = null
    }
    if (!(await this.exists(state.heartbeatId))) {
      state.heartbeatId = await this.createJson(HEARTBEAT_NAME, state.rootId, { alive_at: null })
    }
    this.saveState(state)
    return state
  }

  async readJson(id) {
    const res = await this.request(`${API}/files/${id}?alt=media`)
    const text = await res.text()
    try {
      return JSON.parse(text)
    } catch {
      throw new DriveError('The file in Google Drive is not valid JSON.')
    }
  }

  /** Resumable upload (works for multi-hundred-MB recordings). */
  async uploadFile(name, parent, filePath, mimeType) {
    const size = fs.statSync(filePath).size
    const init = await this.request(`${UPLOAD}/files?uploadType=resumable&fields=id`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json; charset=UTF-8',
        'X-Upload-Content-Type': mimeType,
        'X-Upload-Content-Length': String(size),
      },
      body: JSON.stringify({ name, parents: [parent] }),
    })
    const location = init.headers.get('location')
    if (!location) throw new DriveError('Google Drive did not return an upload session.')
    const res = await this.request(
      location,
      {
        method: 'PUT',
        headers: { 'Content-Type': mimeType, 'Content-Length': String(size) },
        body: fs.readFileSync(filePath),
      },
      10 * 60 * 1000,
    )
    return (await res.json()).id
  }

  async deleteFile(id) {
    if (!id) return
    await this.request(`${API}/files/${id}`, { method: 'DELETE' }).catch(() => {})
  }
}

module.exports = { Drive, DriveError, ROOT_NAME, HEARTBEAT_NAME }
