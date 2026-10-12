// Google OAuth for installed apps: system browser + loopback redirect + PKCE.
// The refresh token is encrypted with the OS keystore (Electron safeStorage → DPAPI on Windows).
const crypto = require('node:crypto')
const fs = require('node:fs')
const http = require('node:http')
const path = require('node:path')
const { safeStorage, shell } = require('electron')

const SCOPE = 'https://www.googleapis.com/auth/drive.file'
const AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
const TOKEN_URL = 'https://oauth2.googleapis.com/token'
const SIGN_IN_TIMEOUT_MS = 5 * 60 * 1000

class AuthError extends Error {}

const b64url = (buf) => buf.toString('base64url')

class GoogleAuth {
  constructor(config, userDataDir) {
    this.config = config
    this.tokenFile = path.join(userDataDir, 'google-token.bin')
    this.access = null // { token, expiresAt }
  }

  isConfigured() {
    return Boolean(this.config.clientId && this.config.clientSecret)
  }

  hasStoredToken() {
    return fs.existsSync(this.tokenFile)
  }

  readRefreshToken() {
    if (!this.hasStoredToken()) return null
    if (!safeStorage.isEncryptionAvailable()) throw new AuthError('OS credential encryption is unavailable.')
    return safeStorage.decryptString(fs.readFileSync(this.tokenFile))
  }

  saveRefreshToken(token) {
    if (!safeStorage.isEncryptionAvailable()) throw new AuthError('OS credential encryption is unavailable.')
    fs.writeFileSync(this.tokenFile, safeStorage.encryptString(token))
  }

  signOut() {
    this.access = null
    fs.rmSync(this.tokenFile, { force: true })
  }

  /** Opens the system browser and waits for the loopback redirect. */
  async signIn() {
    if (!this.isConfigured()) throw new AuthError('Google OAuth client is not configured.')
    const verifier = b64url(crypto.randomBytes(32))
    const challenge = b64url(crypto.createHash('sha256').update(verifier).digest())
    const state = b64url(crypto.randomBytes(16))

    const { code, redirectUri } = await new Promise((resolve, reject) => {
      const server = http.createServer((req, res) => {
        const url = new URL(req.url, 'http://127.0.0.1')
        if (url.pathname !== '/') {
          res.writeHead(404).end()
          return
        }
        const ok = url.searchParams.get('state') === state && url.searchParams.get('code')
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' })
        res.end(
          ok
            ? '<h2>SpeakWise is connected.</h2><p>You can close this tab and return to the app.</p>'
            : '<h2>Sign-in was not completed.</h2><p>Return to SpeakWise and try again.</p>',
        )
        clearTimeout(timer)
        server.close()
        if (ok) resolve({ code: url.searchParams.get('code'), redirectUri })
        else reject(new AuthError(url.searchParams.get('error') || 'Sign-in was cancelled.'))
      })
      const timer = setTimeout(() => {
        server.close()
        reject(new AuthError('Sign-in timed out.'))
      }, SIGN_IN_TIMEOUT_MS)
      let redirectUri
      server.listen(0, '127.0.0.1', () => {
        redirectUri = `http://127.0.0.1:${server.address().port}`
        const params = new URLSearchParams({
          client_id: this.config.clientId,
          redirect_uri: redirectUri,
          response_type: 'code',
          scope: SCOPE,
          code_challenge: challenge,
          code_challenge_method: 'S256',
          state,
          access_type: 'offline',
          prompt: 'consent',
        })
        shell.openExternal(`${AUTH_URL}?${params}`)
      })
    })

    const tokens = await this.tokenRequest({
      grant_type: 'authorization_code',
      code,
      code_verifier: verifier,
      redirect_uri: redirectUri,
    })
    if (!tokens.refresh_token) throw new AuthError('Google did not return a refresh token.')
    this.saveRefreshToken(tokens.refresh_token)
    this.setAccess(tokens)
  }

  setAccess(tokens) {
    this.access = { token: tokens.access_token, expiresAt: Date.now() + (tokens.expires_in - 60) * 1000 }
  }

  async tokenRequest(body) {
    const res = await fetch(TOKEN_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        client_id: this.config.clientId,
        client_secret: this.config.clientSecret,
        ...body,
      }),
      signal: AbortSignal.timeout(20000),
    })
    const json = await res.json().catch(() => ({}))
    if (!res.ok) {
      // invalid_grant = revoked/expired refresh token; drop it so the UI asks to reconnect.
      if (json.error === 'invalid_grant') this.signOut()
      throw new AuthError(`Google token request failed (${json.error || res.status}).`)
    }
    return json
  }

  async getAccessToken() {
    if (this.access && Date.now() < this.access.expiresAt) return this.access.token
    const refresh = this.readRefreshToken()
    if (!refresh) throw new AuthError('Not connected to Google.')
    this.setAccess(await this.tokenRequest({ grant_type: 'refresh_token', refresh_token: refresh }))
    return this.access.token
  }
}

module.exports = { GoogleAuth, AuthError, SCOPE }
