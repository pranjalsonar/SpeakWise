// Launches Electron.
//   --smoke  load the UI in smoke mode (see main.cjs) with a throwaway profile
//   --shots  capture screenshots into docs/desktop-screenshots (see lib/shots.cjs)
const { spawnSync } = require('node:child_process')
const os = require('node:os')
const path = require('node:path')
const electron = require('electron')

const smoke = process.argv.includes('--smoke')
const shots = process.argv.includes('--shots')
// Set by VS Code terminals; it would make Electron run as plain Node.
delete process.env.ELECTRON_RUN_AS_NODE

const env = { ...process.env }
if (smoke) env.SPEAKWISE_SMOKE = '1'
if (shots) env.SPEAKWISE_SHOTS = path.join(__dirname, '..', '..', 'docs', 'desktop-screenshots')

const args = ['.']
if (smoke || shots) args.push(`--user-data-dir=${path.join(os.tmpdir(), `speakwise-run-${Date.now()}`)}`)
const res = spawnSync(electron, args, {
  cwd: path.join(__dirname, '..'),
  env,
  stdio: 'inherit',
  timeout: smoke ? 60000 : shots ? 300000 : undefined,
})
process.exit(res.status ?? 1)
