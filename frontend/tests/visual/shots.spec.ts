import { test, type Page } from '@playwright/test'

// Run: npm run shots                     (all screens)
//      npm run shots -- -g "03-home"     (one screen)
// Output: tests/visual/__shots__/<project>/<name>.png

type Auth = 'student' | 'admin' | 'new'

interface Shot {
  name: string
  path: string
  auth?: Auth
  /** Partial session state written to sessionStorage before load. */
  session?: Record<string, unknown>
  /** Interactions to reach the state being captured. */
  prepare?: (page: Page, isMobile: boolean) => Promise<void>
  fullPage?: boolean
}

const users: Record<Auth, object> = {
  student: { name: 'Priya Sharma', firstName: 'Priya', email: 'priya.sharma@example.com', initials: 'PS', role: 'student' },
  new: { name: 'Sam Rivera', firstName: 'Sam', email: 'sam.rivera@example.com', initials: 'SR', role: 'student' },
  admin: { name: 'Admin', firstName: 'Admin', email: 'admin@speakwise.app', initials: 'AD', role: 'admin' },
}

const fastFashion = { id: 't3', title: 'Fast fashion and its environmental cost', category: 'Environment', difficulty: 'Beginner' }

/** Start a recording, let it run briefly, then end it early to reach Review. */
async function recordAndStop(page: Page) {
  await page.getByRole('button', { name: /^Start/ }).filter({ visible: true }).click()
  await page.waitForTimeout(8000)
  await page.getByRole('button', { name: /^Stop/ }).filter({ visible: true }).click()
  await page.getByRole('button', { name: 'End recording' }).click()
  await page.waitForURL('**/session/review')
  await page.waitForTimeout(500)
}

const shots: Shot[] = [
  { name: '00-dev-ui', path: '/dev/ui' },
  { name: '01-landing', path: '/' },
  { name: '01-landing-full', path: '/', fullPage: true },
  {
    name: '01-landing-menu',
    path: '/',
    prepare: async (page, isMobile) => {
      if (isMobile) await page.getByRole('button', { name: 'Open menu' }).click()
    },
  },
  { name: '02-login', path: '/login' },
  {
    name: '02-login-errors',
    path: '/login',
    prepare: async (page) => {
      await page.getByLabel('Email').fill('not-an-email')
      await page.getByRole('button', { name: 'Log in' }).click()
    },
  },
  {
    name: '02-login-bad-credentials',
    path: '/login',
    prepare: async (page) => {
      await page.getByLabel('Email').fill('priya.sharma@example.com')
      await page.getByLabel('Password', { exact: true }).fill('wrong')
      await page.getByRole('button', { name: 'Log in' }).click()
      await page.getByRole('alert').waitFor()
    },
  },
  { name: '02b-register', path: '/register' },
  {
    name: '02b-register-filled',
    path: '/register',
    prepare: async (page) => {
      await page.getByLabel('Full name').fill('Sam Rivera')
      await page.getByLabel('Email').fill('sam.rivera@example.com')
      await page.getByLabel('Password', { exact: true }).fill('speak2026')
      await page.getByLabel('Confirm password').fill('speak2026')
    },
  },
  { name: '03-home', path: '/home', auth: 'student' },
  { name: '04-home-empty', path: '/home', auth: 'new' },
  { name: '05-topic', path: '/session/topic', auth: 'student', session: { suggestedTopicId: 't3' } },
  {
    name: '05-topic-own',
    path: '/session/topic',
    auth: 'student',
    session: { suggestedTopicId: 't3' },
    prepare: async (page) => {
      await page.getByRole('radio', { name: 'My own topic' }).click()
      await page.getByRole('button', { name: 'Why cities should ban cars' }).click()
    },
  },
  {
    name: '06-prepare',
    path: '/session/prepare',
    auth: 'student',
    session: { step: 'prepare', topic: fastFashion },
    prepare: async (page) => {
      // Scroll the article a little to show reading progress.
      await page.locator('.prepare-page__scroll').evaluate((el) => el.scrollTo(0, (el.scrollHeight - el.clientHeight) * 0.42))
      await page.locator('.prepare-page__scroll').evaluate((el) => el.scrollTo(0, 0))
    },
  },
  {
    name: '07-prepare-confirm',
    path: '/session/prepare',
    auth: 'student',
    session: { step: 'prepare', topic: fastFashion, readPct: 42 },
    prepare: async (page) => {
      await page.getByRole('button', { name: "I'm ready, start talk" }).filter({ visible: true }).click()
      await page.getByRole('dialog').waitFor()
      await page.waitForTimeout(400) // let the open animation finish
    },
  },
  {
    name: '07b-prepare-notes',
    path: '/session/prepare',
    auth: 'student',
    session: { step: 'prepare', topic: fastFashion, readPct: 42 },
    prepare: async (page, isMobile) => {
      if (!isMobile) return
      await page.getByRole('button', { name: 'Notes' }).click()
      await page.getByRole('dialog').waitFor()
      await page.waitForTimeout(400)
    },
  },
  { name: '08-record-camera-check', path: '/session/record', auth: 'student', session: { step: 'record', topic: fastFashion } },
  {
    name: '09-record-countdown',
    path: '/session/record',
    auth: 'student',
    session: { step: 'record', topic: fastFashion },
    prepare: async (page) => {
      await page.getByRole('button', { name: /^Start/ }).filter({ visible: true }).click()
      await page.waitForTimeout(2300)
    },
  },
  {
    name: '10-record-live',
    path: '/session/record',
    auth: 'student',
    session: { step: 'record', topic: fastFashion },
    prepare: async (page) => {
      await page.getByRole('button', { name: /^Start/ }).filter({ visible: true }).click()
      await page.waitForTimeout(7000)
    },
  },
  {
    name: '11-record-end-early',
    path: '/session/record',
    auth: 'student',
    session: { step: 'record', topic: fastFashion },
    prepare: async (page) => {
      await page.getByRole('button', { name: /^Start/ }).filter({ visible: true }).click()
      await page.waitForTimeout(6500)
      await page.getByRole('button', { name: /^Stop/ }).filter({ visible: true }).click()
      await page.getByRole('dialog').waitFor()
      await page.waitForTimeout(400)
    },
  },
  {
    name: '12-review',
    path: '/session/record',
    auth: 'student',
    session: { step: 'record', topic: fastFashion },
    prepare: async (page) => {
      await recordAndStop(page)
    },
  },
  {
    name: '13-processing',
    path: '/session/record',
    auth: 'student',
    session: { step: 'record', topic: fastFashion },
    prepare: async (page) => {
      await recordAndStop(page)
      await page.getByRole('button', { name: 'Submit for feedback' }).filter({ visible: true }).click()
      await page.waitForTimeout(1200)
    },
  },
  {
    name: '14-feedback',
    path: '/feedback/s1',
    auth: 'student',
    prepare: async (page) => {
      await page.getByRole('button', { name: /Transcript/ }).click()
    },
  },
  { name: '14-feedback-full', path: '/feedback/s1', auth: 'student', fullPage: true },
  { name: '15-history', path: '/history', auth: 'student' },
  {
    name: '15-history-empty',
    path: '/history',
    auth: 'student',
    prepare: async (page) => {
      await page.getByRole('searchbox').fill('zzz')
    },
  },
  { name: '16-profile', path: '/profile', auth: 'student' },
  { name: '17-admin-dashboard', path: '/admin', auth: 'admin' },
  { name: '18-admin-users', path: '/admin/users', auth: 'admin' },
  {
    name: '19-admin-add-user',
    path: '/admin/users',
    auth: 'admin',
    prepare: async (page) => {
      await page.getByRole('button', { name: 'Add user' }).filter({ visible: true }).first().click()
      await page.getByRole('dialog').waitFor()
      await page.getByRole('dialog').getByRole('button', { name: 'Add user' }).click()
      await page.waitForTimeout(400)
    },
  },
  {
    name: '19b-admin-user-added',
    path: '/admin/users',
    auth: 'admin',
    prepare: async (page) => {
      await page.getByRole('button', { name: 'Add user' }).filter({ visible: true }).first().click()
      const dialog = page.getByRole('dialog')
      await dialog.getByLabel('Full name').fill('Nina Patel')
      await dialog.getByLabel('Email').fill('nina.patel@example.com')
      await dialog.getByRole('button', { name: 'Add user' }).click()
      await dialog.waitFor({ state: 'detached' })
      await page.waitForTimeout(300)
    },
  },
]

for (const shot of shots) {
  test(shot.name, async ({ page }, testInfo) => {
    const isMobile = testInfo.project.name === 'mobile'
    await page.addInitScript(
      ({ user, session }) => {
        if (user) localStorage.setItem('sw.auth', JSON.stringify(user))
        if (session) {
          sessionStorage.setItem(
            'sw.session',
            JSON.stringify({ step: 'topic', mode: 'suggest', category: 'All', suggestedTopicId: null, ownTopic: '', durationMin: 3, topic: null, readPct: 0, notes: '', textStep: 0, recording: null, feedbackSessionId: null, ...session }),
          )
        }
      },
      { user: shot.auth ? users[shot.auth] : null, session: shot.session ?? null },
    )
    await page.goto(shot.path)
    await page.evaluate(() => document.fonts.ready)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(600) // let mock services resolve
    if (shot.prepare) await shot.prepare(page, isMobile)
    await page.screenshot({
      path: `tests/visual/__shots__/${testInfo.project.name}/${shot.name}.png`,
      fullPage: shot.fullPage,
    })
  })
}
