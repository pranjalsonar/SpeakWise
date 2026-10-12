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

/** GET /api/v1/admin/dashboard response with the design's numbers. */
const dashboardFixture = {
  generated_at: '2026-09-27T09:00:00Z',
  timezone: 'Asia/Kolkata',
  kpis: {
    total_users: 1248, new_users_this_month: 64, active_users: 890, active_users_pct: 71.3,
    total_sessions: 5630, sessions_this_week: 768, minutes_spoken: 14215, avg_minutes_per_session: 2.5,
    average_score: 74, average_score_change_vs_last_month: 3,
  },
  sessions_per_week: [
    ['2026-08-03', 420], ['2026-08-10', 468], ['2026-08-17', 455], ['2026-08-24', 512],
    ['2026-08-31', 590], ['2026-09-07', 634], ['2026-09-14', 702], ['2026-09-21', 768],
  ].map(([week_start, count]) => ({ week_start, count })),
  sessions_by_category: [
    ['Technology', 28], ['Business', 24], ['Society', 19], ['Environment', 16], ['Science', 13],
  ].map(([category, pct]) => ({ category, count: pct, pct })),
  recent_sessions: [
    ['Mei Tanaka', 'Space exploration: worth the cost?', 81, 12],
    ['Arjun Mehta', 'The case for a four-day work week', 88, 40],
    ['Priya Sharma', 'Fast fashion and its environmental cost', 78, 120],
    ['Hannah Weber', 'CRISPR and the ethics of gene editing', 73, 180],
    ['Sara Okafor', 'Is social media making us lonelier?', 69, 300],
  ].map(([user_name, topic, score, minutesAgo], i) => ({
    id: i + 1, user_name, topic, score,
    created_at: new Date(Date.now() - Number(minutesAgo) * 60_000).toISOString(),
  })),
}

const fastFashion = { id: '19', title: 'Fast fashion and its environmental cost', category: 'Environment', difficulty: 'Beginner' }
const fastFashionTopic = { ...fastFashion, teaser: 'Cheap clothes, fast trends, and a planet paying the difference.' }
const keyPoints = [
  'What defines fast fashion',
  'Environmental impact (water, carbon, waste)',
  'Human and labour costs',
  'Role of consumers',
  'Solutions: circular fashion, regulation, buying less',
]

/** Topics API fixtures (the design's fast-fashion example). */
const topicDto = (topic: typeof fastFashionTopic, source = 'curated') => ({
  id: Number(topic.id), title: topic.title, teaser: topic.teaser, category: topic.category,
  difficulty: topic.difficulty, source, recorded: false,
})
const dailyFixture = {
  date: '2026-09-27',
  topic: topicDto({ id: '1', title: 'Should AI tutors replace homework help?', category: 'Technology', difficulty: 'Intermediate', teaser: 'AI can explain anything at 2 a.m.' }),
}
const readingFixture = {
  id: 7, topic: topicDto(fastFashionTopic), version: 1, is_repeat: false, lang: 'en',
  summary: 'Fast fashion is a business model built on speed.',
  key_points: keyPoints,
  sections: [
    { heading: 'What is fast fashion?', paragraphs: [
      'Fast fashion is a business model built on speed: trend-driven clothing designed, produced, and sold in a matter of weeks at very low prices. Brands release new collections constantly, encouraging shoppers to buy more and wear items fewer times. The result is an industry that produces over 100 billion garments a year, and a growing mountain of textile waste.',
      'The model depends on three things: cheap materials such as polyester, low-cost labour, and supply chains that can turn a sketch into a store rack in under a month.' ] },
    { heading: 'The true cost of a $5 T-shirt', paragraphs: [
      'A low price tag hides costs that never show up at the till. Growing cotton, dyeing fabric and shipping finished garments around the world all draw on resources that are rarely priced in. The fashion industry is estimated to produce up to 10% of global carbon emissions.' ] },
    { heading: 'Water, waste and microplastics', paragraphs: [
      'A single cotton T-shirt can take around 2,700 litres of water to produce. Synthetic fabrics bring a different problem: every wash sheds tiny plastic fibres that travel through wastewater into rivers and oceans.',
      'Meanwhile, the equivalent of one rubbish truck of textiles is landfilled or burned every second.' ] },
    { heading: 'Who pays the price?', paragraphs: [
      'Most garments are sewn in countries where wages are low and labour protections are weak. The 2013 Rana Plaza collapse in Bangladesh, which killed more than 1,100 garment workers, drew global attention to unsafe factories.' ] },
    { heading: 'What can change?', paragraphs: [
      'Solutions work at several levels. Circular fashion keeps clothes in use longer through repair, resale and recycling. For shoppers, the most effective step is also the simplest: buy less, and wear what you own for longer.' ] },
  ],
  word_count: 2800, read_minutes: 15,
  sources: [{ title: 'Fast fashion', url: 'https://en.wikipedia.org/wiki/Fast_fashion?oldid=1', lang: 'en', revision_id: 1 }],
  license: 'CC BY-SA 4.0', license_url: 'https://creativecommons.org/licenses/by-sa/4.0/',
  attribution: 'Adapted from Wikipedia articles "Fast fashion", licensed under CC BY-SA 4.0.',
  related_topics: [],
}

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
  { name: '05-topic', path: '/session/topic', auth: 'student', session: { suggestedTopic: fastFashionTopic } },
  {
    name: '05-topic-own',
    path: '/session/topic',
    auth: 'student',
    session: { suggestedTopic: fastFashionTopic },
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
  { name: '08-record-camera-check', path: '/session/record', auth: 'student', session: { step: 'record', topic: fastFashion, keyPoints } },
  {
    name: '09-record-countdown',
    path: '/session/record',
    auth: 'student',
    session: { step: 'record', topic: fastFashion, keyPoints },
    prepare: async (page) => {
      await page.getByRole('button', { name: /^Start/ }).filter({ visible: true }).click()
      await page.waitForTimeout(2300)
    },
  },
  {
    name: '10-record-live',
    path: '/session/record',
    auth: 'student',
    session: { step: 'record', topic: fastFashion, keyPoints },
    prepare: async (page) => {
      await page.getByRole('button', { name: /^Start/ }).filter({ visible: true }).click()
      await page.waitForTimeout(7000)
    },
  },
  {
    name: '11-record-end-early',
    path: '/session/record',
    auth: 'student',
    session: { step: 'record', topic: fastFashion, keyPoints },
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
    session: { step: 'record', topic: fastFashion, keyPoints },
    prepare: async (page) => {
      await recordAndStop(page)
    },
  },
  {
    name: '13-processing',
    path: '/session/record',
    auth: 'student',
    session: { step: 'record', topic: fastFashion, keyPoints },
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
      await dialog.getByText('Share this temporary password').waitFor()
      await page.waitForTimeout(300)
    },
  },
]

/** GET /api/v1/users rows built from the design's user list. */
const userFixture = (
  [
    [1, 'Priya Sharma', 'priya.sharma@example.com', 12, 0, '2026-08-02', true],
    [2, 'Arjun Mehta', 'arjun.mehta@example.com', 27, 1, '2026-07-14', true],
    [3, 'Sara Okafor', 'sara.okafor@example.com', 8, 3, '2026-08-19', true],
    [4, 'Liam Chen', 'liam.chen@example.com', 3, 25, '2026-08-28', false],
    [5, 'Mei Tanaka', 'mei.tanaka@example.com', 19, 1, '2026-06-30', true],
    [6, 'Diego Alvarez', 'diego.alvarez@example.com', 0, null, '2026-09-21', false],
    [7, 'Hannah Weber', 'hannah.weber@example.com', 14, 2, '2026-07-07', true],
    [8, 'Omar Haddad', 'omar.haddad@example.com', 6, 16, '2026-08-09', true],
  ] as const
).map(([id, full_name, email, session_count, daysAgo, joined, is_active]) => {
  const lastActive =
    daysAgo === null ? null : new Date(Date.now() - daysAgo * 86_400_000).toISOString()
  return {
    id, full_name, email, role_id: 2, role: 'user', is_active, session_count,
    created_at: `${joined}T09:00:00Z`, updated_at: `${joined}T09:00:00Z`,
    last_login_at: lastActive, last_session_at: lastActive, last_active_at: lastActive,
  }
})

const userListFixture = {
  items: userFixture, total: userFixture.length, skip: 0, limit: 50,
  counts: { all: 8, active: 6, inactive: 2 },
}

const createdUserFixture = {
  user: { ...userFixture[0], id: 9, full_name: 'Nina Patel', email: 'nina.patel@example.com',
    session_count: 0, last_login_at: null, last_session_at: null, last_active_at: null },
  temporary_password: 'Xk3v-9pQz_7mT',
}

for (const shot of shots) {
  test(shot.name, async ({ page }, testInfo) => {
    const isMobile = testInfo.project.name === 'mobile'
    // Keep screenshots independent of the backend: fake the API calls the screens make.
    // Login always fails (02-login-bad-credentials), admin screens get fixtures,
    // everything else acts offline so screens keep the user seeded below.
    await page.route('**/api/v1/**', (route) => {
      const { pathname } = new URL(route.request().url())
      const method = route.request().method()
      if (pathname.endsWith('/auth/login'))
        return route.fulfill({ status: 401, json: { detail: 'Invalid email or password' } })
      if (pathname.endsWith('/admin/dashboard')) return route.fulfill({ json: dashboardFixture })
      if (pathname.endsWith('/topics/daily')) return route.fulfill({ json: dailyFixture })
      if (pathname.endsWith('/topics/suggest'))
        return route.fulfill({ json: { topic: topicDto(fastFashionTopic), all_recorded: false } })
      if (pathname.endsWith('/topics/custom'))
        return route.fulfill({ status: 201, json: { topic: { ...topicDto(fastFashionTopic, 'custom'), id: 40, category: null }, created: true } })
      if (pathname.endsWith('/reading-material')) return route.fulfill({ json: readingFixture })
      if (pathname.endsWith('/users') && method === 'GET')
        return route.fulfill({ json: userListFixture })
      if (pathname.endsWith('/users') && method === 'POST')
        return route.fulfill({ status: 201, json: createdUserFixture })
      return route.abort()
    })
    await page.addInitScript(
      ({ user, session }) => {
        if (user) {
          sessionStorage.setItem('sw.auth', JSON.stringify(user))
          // A saved user only counts with an unexpired token (see AuthProvider.restoreUser).
          const expiresAt = new Date(Date.now() + 60 * 60 * 1000).toISOString()
          sessionStorage.setItem('sw.token', JSON.stringify({ accessToken: 'visual-test', expiresAt }))
        }
        if (session) {
          sessionStorage.setItem(
            'sw.session',
            JSON.stringify({ step: 'topic', mode: 'suggest', category: 'All', suggestedTopic: null, ownTopic: '', durationMin: 3, topic: null, readingMaterialId: null, keyPoints: [], readPct: 0, notes: '', textStep: 0, recording: null, feedbackSessionId: null, ...session }),
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
