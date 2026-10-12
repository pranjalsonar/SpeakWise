// Runtime configuration. Secrets never live in source control: the OAuth client is read from
// environment variables or from a JSON file the developer creates (see README).
const fs = require('node:fs')
const path = require('node:path')

const DEFAULT_NOTEBOOK_URL =
  'https://colab.research.google.com/github/pranjalsonar/SpeakWise/blob/main/speakwise_pipeline/notebooks/speakwise_pipeline_colab.ipynb'

function readJson(file) {
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'))
  } catch {
    return null
  }
}

/** Looks in userData/speakwise.config.json first, then desktop/speakwise.config.json. */
function loadConfig(userDataDir) {
  const candidates = [
    path.join(userDataDir, 'speakwise.config.json'),
    path.join(__dirname, '..', 'speakwise.config.json'),
  ]
  const file = candidates.find((f) => fs.existsSync(f))
  const json = (file && readJson(file)) || {}
  return {
    configFile: file || null,
    clientId: process.env.SPEAKWISE_GOOGLE_CLIENT_ID || json.googleClientId || '',
    clientSecret: process.env.SPEAKWISE_GOOGLE_CLIENT_SECRET || json.googleClientSecret || '',
    notebookUrl: process.env.SPEAKWISE_COLAB_NOTEBOOK_URL || json.colabNotebookUrl || DEFAULT_NOTEBOOK_URL,
    searchedPaths: candidates,
  }
}

module.exports = { loadConfig }
