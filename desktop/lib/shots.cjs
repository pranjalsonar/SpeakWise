// Screenshot mode (`npm run shots`): drives the real UI with Chromium's synthetic camera/microphone
// (a test pattern and a beep) and saves a PNG of each screen. Nothing is faked in the app itself:
// without a Google connection the run ends on the real "Upload failed" state.
const fs = require('node:fs')
const path = require('node:path')

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

async function runShots(win, app, uiEntry, outDir) {
  fs.mkdirSync(outDir, { recursive: true })
  const wc = win.webContents
  const js = (code) => wc.executeJavaScript(code)
  const text = () => js('document.body.innerText')

  async function waitFor(needle, timeoutMs = 20000) {
    const end = Date.now() + timeoutMs
    while (Date.now() < end) {
      if ((await text()).includes(needle)) return
      await sleep(250)
    }
    throw new Error(`Timed out waiting for "${needle}"`)
  }

  async function click(label) {
    const ok = await js(`(() => {
      const b = [...document.querySelectorAll('button')].find((el) => el.innerText.trim().startsWith(${JSON.stringify(label)}))
      if (b) b.click()
      return Boolean(b)
    })()`)
    if (!ok) throw new Error(`No button "${label}"`)
  }

  async function shot(name) {
    await sleep(700) // let fonts/animations settle
    const image = await wc.capturePage()
    fs.writeFileSync(path.join(outDir, `${name}.png`), image.toPNG())
    console.log('saved', name)
  }

  const loaded = () => new Promise((r) => wc.once('did-finish-load', r))

  try {
    await loaded()
    await waitFor('Connect to the analysis workflow')
    await shot('01-connect')

    // The connection screen only offers Continue once Drive is reachable, so start at Welcome.
    const next = loaded()
    win.loadFile(uiEntry, { query: { screen: 'welcome' } })
    await next
    await waitFor('Random Topic')
    await shot('02-welcome')

    await click('Random Topic')
    await waitFor('Continue to Speaking')
    await shot('03-reading')

    await click('Continue to Speaking')
    await waitFor('How long will you speak?')
    await click('1 minute')
    await shot('04-duration')

    await click('Set up camera')
    await waitFor('Start recording')
    await shot('05-camera-preview')

    await click('Start recording')
    await waitFor('REC')
    await sleep(3000)
    await shot('06-recording')

    // Real 60 s recording, auto-stop, MP4 conversion and validation.
    await waitFor('Upload and analyse', 120000)
    await shot('07-consent')

    await click('Upload and analyse')
    await waitFor('Analyzing Your Speech')
    await sleep(4000)
    await shot('08-analyzing')
    app.exit(0)
  } catch (error) {
    console.error('SHOTS FAILED:', error.message)
    await shot('error-state').catch(() => {})
    app.exit(1)
  }
}

module.exports = { runShots }
