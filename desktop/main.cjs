// SpeakWise desktop shell. One in-memory session at a time; no database, no local inference.
const crypto = require('node:crypto')
const fs = require('node:fs')
const os = require('node:os')
const path = require('node:path')
const { app, BrowserWindow, dialog, ipcMain, session: electronSession, shell } = require('electron')
const { loadConfig } = require('./lib/config.cjs')
const { GoogleAuth } = require('./lib/oauth.cjs')
const { Drive } = require('./lib/drive.cjs')
const { toValidatedMp4 } = require('./lib/media.cjs')
const { checkStartInput } = require('./lib/validate.cjs')

const UI_ENTRY = path.join(__dirname, '..', 'frontend', 'dist-desktop', 'desktop.html')
const HEARTBEAT_FRESH_S = 120
const MAX_RECORDING_BYTES = 1024 * 1024 * 1024

let config, auth, drive, win
/** The single active session (null when idle). */
let active = null

// ------------------------------------------------------------------ helpers
const ok = (data = {}) => ({ ok: true, ...data })
const fail = (error) => ({ ok: false, error: error instanceof Error ? error.message : String(error) })

function handle(channel, fn) {
  ipcMain.handle(channel, async (event, ...args) => {
    // Only our own window/page may call the API.
    if (!win || event.sender !== win.webContents || !event.senderFrame?.url.startsWith('file://')) {
      return fail('Unauthorized caller.')
    }
    try {
      return await fn(...args)
    } catch (error) {
      console.error(`[${channel}]`, error.message) // never log tokens; messages carry none
      return fail(error)
    }
  })
}

async function heartbeat(state) {
  try {
    const beat = await drive.readJson(state.heartbeatId)
    if (!beat?.alive_at) return { workerAlive: false, heartbeatAgeS: null }
    const age = Math.max(0, (Date.now() - Date.parse(beat.alive_at)) / 1000)
    return { workerAlive: age < HEARTBEAT_FRESH_S, heartbeatAgeS: Math.round(age) }
  } catch {
    return { workerAlive: false, heartbeatAgeS: null }
  }
}

function removeLocal(s) {
  if (s?.dir) fs.rmSync(s.dir, { recursive: true, force: true })
}

async function removeRemote(s) {
  if (!s?.remote) return
  for (const id of [s.remote.recordingId, s.remote.sessionFileId, s.remote.reportId]) await drive.deleteFile(id)
}

// ------------------------------------------------------------------ connection
handle('connection:status', async () => {
  const base = {
    configured: auth.isConfigured(),
    configHint: auth.isConfigured()
      ? null
      : `Google OAuth client not configured. Create speakwise.config.json in one of: ${config.searchedPaths.join(' | ')} (see desktop/README.md).`,
    authorized: false,
    driveReady: false,
    workerAlive: false,
    heartbeatAgeS: null,
    notebookUrl: config.notebookUrl,
    detail: null,
  }
  if (!base.configured || !auth.hasStoredToken()) return ok(base)
  try {
    await auth.getAccessToken()
    base.authorized = true
    const state = await drive.ensureWorkspace()
    base.driveReady = true
    Object.assign(base, await heartbeat(state))
  } catch (error) {
    base.detail = error.message
  }
  return ok(base)
})

handle('connection:signIn', async () => {
  await auth.signIn()
  return ok()
})

handle('connection:signOut', async () => {
  auth.signOut()
  return ok()
})

handle('connection:openNotebook', async () => {
  if (!/^https:\/\/colab\.research\.google\.com\//.test(config.notebookUrl)) return fail('Configured notebook URL is not a Colab URL.')
  await shell.openExternal(config.notebookUrl)
  return ok()
})

// ------------------------------------------------------------------ session
handle('session:start', async (input) => {
  const error = checkStartInput(input)
  if (error) return fail(error)
  await discardActive()
  const id = `sw-${new Date().toISOString().replace(/[-:T.Z]/g, '').slice(0, 14)}-${crypto.randomBytes(4).toString('hex')}`
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'speakwise-'))
  active = { id, dir, topic: input.topic, readingMaterial: input.readingMaterial, durationS: input.durationS, mp4: null, remote: null }
  return ok({ sessionId: id })
})

handle('session:saveRecording', async (sessionId, bytes, mimeType) => {
  if (!active || sessionId !== active.id) return fail('No matching active session.')
  if (!(bytes instanceof Uint8Array) || bytes.byteLength === 0) return fail('The recording is empty.')
  if (bytes.byteLength > MAX_RECORDING_BYTES) return fail('The recording is too large.')
  if (typeof mimeType !== 'string') return fail('Unknown recording format.')
  const isMp4 = mimeType.startsWith('video/mp4')
  const raw = path.join(active.dir, isMp4 ? 'raw.mp4' : 'raw.webm')
  fs.writeFileSync(raw, bytes)
  const out = path.join(active.dir, 'recording.mp4')
  const info = await toValidatedMp4(raw, out, isMp4)
  fs.rmSync(raw, { force: true })
  active.mp4 = out
  return ok({ durationS: info.durationS, sizeBytes: fs.statSync(out).size })
})

handle('session:submit', async (sessionId) => {
  if (!active || sessionId !== active.id) return fail('No matching active session.')
  if (!active.mp4) return fail('No recording to submit.')
  if (active.remote) return ok() // already uploaded; just keep waiting
  const state = await drive.ensureWorkspace()
  const remote = {}
  try {
    remote.reportId = await drive.createJson(`report_${active.id}.json`, state.rootId, { status: 'pending', session_id: active.id })
    remote.recordingId = await drive.uploadFile(`recording_${active.id}.mp4`, state.rootId, active.mp4, 'video/mp4')
    // Written last: the notebook only picks up sessions whose session file exists.
    remote.sessionFileId = await drive.createJson(`session_${active.id}.json`, state.rootId, {
      session_id: active.id,
      topic: active.topic,
      reading_material: active.readingMaterial,
      speaking_duration_s: active.durationS,
      recording_file_id: remote.recordingId,
      report_file_id: remote.reportId,
      created_at: new Date().toISOString(),
    })
  } catch (error) {
    for (const id of Object.values(remote)) await drive.deleteFile(id)
    throw error
  }
  active.remote = remote
  return ok()
})

handle('session:poll', async (sessionId) => {
  if (!active || sessionId !== active.id || !active.remote) return fail('No submitted session.')
  const state = await drive.ensureWorkspace()
  const [envelope, beat] = await Promise.all([drive.readJson(active.remote.reportId), heartbeat(state)])
  return ok({ envelope, ...beat })
})

handle('session:importReport', async (sessionId) => {
  if (!active || sessionId !== active.id) return fail('No matching active session.')
  const pick = await dialog.showOpenDialog(win, { properties: ['openFile'], filters: [{ name: 'Report', extensions: ['json'] }] })
  if (pick.canceled || !pick.filePaths[0]) return ok({ canceled: true })
  const file = pick.filePaths[0]
  if (fs.statSync(file).size > 50 * 1024 * 1024) return fail('That file is too large to be a report.')
  try {
    return ok({ envelope: JSON.parse(fs.readFileSync(file, 'utf8')) })
  } catch {
    return fail('That file is not valid JSON.')
  }
})

async function discardActive() {
  const s = active
  active = null
  if (!s) return
  removeLocal(s)
  await removeRemote(s).catch(() => {})
}

// Completion and discard both remove the recording locally and from Drive.
handle('session:finish', async (sessionId) => {
  if (active && sessionId === active.id) await discardActive()
  return ok()
})

// ------------------------------------------------------------------ window
function createWindow() {
  win = new BrowserWindow({
    width: 1280,
    height: 860,
    minWidth: 900,
    minHeight: 640,
    backgroundColor: '#f5ead8',
    title: 'SpeakWise',
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      sandbox: true,
      nodeIntegration: false,
      webSecurity: true,
    },
  })
  win.setMenuBarVisibility(false)
  win.webContents.setWindowOpenHandler(() => ({ action: 'deny' }))
  win.webContents.on('will-navigate', (event) => event.preventDefault())
  win.loadFile(UI_ENTRY)

  if (process.env.SPEAKWISE_SHOTS) require('./lib/shots.cjs').runShots(win, app, UI_ENTRY, process.env.SPEAKWISE_SHOTS)

  // `npm run smoke`: load the UI, report renderer errors, exit.
  if (process.env.SPEAKWISE_SMOKE) {
    let errors = 0
    win.webContents.on('console-message', (e) => {
      if (e.level === 'error') {
        errors++
        console.error('[renderer]', e.message)
      }
    })
    win.webContents.on('did-finish-load', () =>
      setTimeout(async () => {
        const text = await win.webContents.executeJavaScript('document.body.innerText')
        const ok = errors === 0 && text.includes('Connect to the analysis workflow')
        console.log(ok ? 'SMOKE OK' : 'SMOKE FAILED', JSON.stringify(text.slice(0, 300)))
        app.exit(ok ? 0 : 1)
      }, 3000),
    )
  }
}

if (process.env.SPEAKWISE_SHOTS) {
  // Synthetic camera + microphone for the screenshot run only.
  app.commandLine.appendSwitch('use-fake-device-for-media-stream')
  app.commandLine.appendSwitch('use-fake-ui-for-media-stream')
}

app.whenReady().then(() => {
  config = loadConfig(app.getPath('userData'))
  auth = new GoogleAuth(config, app.getPath('userData'))
  drive = new Drive(auth, app.getPath('userData'))

  const ses = electronSession.defaultSession
  // Camera + microphone only, and only for our local page.
  ses.setPermissionRequestHandler((wc, permission, callback, details) => {
    callback(permission === 'media' && details.requestingUrl.startsWith('file://') && wc === win?.webContents)
  })
  ses.setPermissionCheckHandler((_wc, permission, origin) => permission === 'media' && origin.startsWith('file://'))

  if (!fs.existsSync(UI_ENTRY)) {
    dialog.showErrorBox('SpeakWise', `UI not built. Run "npm start" in the desktop folder.\nMissing: ${UI_ENTRY}`)
    app.quit()
    return
  }
  createWindow()
})

app.on('window-all-closed', async () => {
  // Keep Drive inputs if analysis may still be running, so the session is not lost mid-run;
  // local temp files go either way.
  if (active) removeLocal(active)
  app.quit()
})
