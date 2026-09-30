// SpeakWise dummy data, from design_handoff_speakwise/mockData.ts.
// Only src/core/services may import this file. Screens get data through services.
import type {
  AdminKpi,
  AdminRecentSession,
  AdminUser,
  ArticleSection,
  CategoryFilter,
  CategoryShare,
  DeviceOptions,
  FeedbackReport,
  LandingFeature,
  Preferences,
  Role,
  Session,
  Stats,
  Topic,
  WeeklyCount,
} from '../types'

export const user = {
  name: 'Priya Sharma',
  firstName: 'Priya',
  email: 'priya.sharma@example.com',
  initials: 'PS',
}

export const stats: Stats = { sessionsCompleted: 12, minutesSpoken: 38, streakDays: 4 }

export const categories: CategoryFilter[] = [
  'All',
  'Technology',
  'Environment',
  'Business',
  'Society',
  'Science',
]
export const durations = [1, 3, 5] as const

export const topics: Topic[] = [
  { id: 't1', title: 'Should AI tutors replace homework help?', category: 'Technology', difficulty: 'Intermediate', teaser: 'AI can explain anything at 2 a.m. Does that make homework help better, or just easier?' },
  { id: 't2', title: 'The case for a four-day work week', category: 'Business', difficulty: 'Intermediate', teaser: 'Trials report happier staff and steady output. Can every industry make it work?' },
  { id: 't3', title: 'Fast fashion and its environmental cost', category: 'Environment', difficulty: 'Beginner', teaser: 'Cheap clothes, fast trends, and a planet paying the difference.' },
  { id: 't4', title: 'Is social media making us lonelier?', category: 'Society', difficulty: 'Beginner', teaser: 'More connected than ever, yet loneliness is rising. Is the feed to blame?' },
  { id: 't5', title: 'CRISPR and the ethics of gene editing', category: 'Science', difficulty: 'Advanced', teaser: 'We can now edit genes precisely. Where should the line be drawn?' },
  { id: 't6', title: 'Remote work vs. office culture', category: 'Business', difficulty: 'Beginner', teaser: 'Flexibility against face time: what really makes teams work?' },
  { id: 't7', title: 'Space exploration: worth the cost?', category: 'Science', difficulty: 'Intermediate', teaser: 'Billions for rockets while problems remain on Earth. Is it worth it?' },
]

export const todaysTopicId = 't1'
export const ownTopicExamples = [
  'My favourite book and why',
  'Why cities should ban cars',
  'The best advice I have received',
]

export const recentSessions: Session[] = [
  { id: 's1', topicTitle: 'Fast fashion and its environmental cost', category: 'Environment', durationMin: 3, date: 'Sep 25', score: 78, status: 'completed' },
  { id: 's2', topicTitle: 'Is social media making us lonelier?', category: 'Society', durationMin: 1, date: 'Sep 23', score: 71, status: 'completed' },
  { id: 's3', topicTitle: 'The case for a four-day work week', category: 'Business', durationMin: 5, date: 'Sep 20', score: 84, status: 'completed' },
  { id: 's4', topicTitle: 'Remote work vs. office culture', category: 'Business', durationMin: 3, date: 'Sep 18', score: null, status: 'processing' },
]

export const keyPoints = [
  'What defines fast fashion',
  'Environmental impact (water, carbon, waste)',
  'Human and labour costs',
  'Role of consumers',
  'Solutions: circular fashion, regulation, buying less',
]

export const article = {
  topicId: 't3',
  readMinutes: 15,
  wordCount: 2800,
  sections: [
    { heading: 'What is fast fashion?', showKeyPoints: true, paragraphs: [
      'Fast fashion is a business model built on speed: trend-driven clothing designed, produced, and sold in a matter of weeks at very low prices. Brands release new collections constantly, encouraging shoppers to buy more and wear items fewer times. The result is an industry that produces over 100 billion garments a year, and a growing mountain of textile waste.',
      'The model depends on three things: cheap materials such as polyester, low-cost labour, and supply chains that can turn a sketch into a store rack in under a month.' ] },
    { heading: 'The true cost of a $5 T-shirt', pullQuote: 'The price on the tag is only part of what a garment costs.', paragraphs: [
      'A low price tag hides costs that never show up at the till. Growing cotton, dyeing fabric and shipping finished garments around the world all draw on resources that are rarely priced in. The fashion industry is estimated to produce up to 10% of global carbon emissions.' ] },
    { heading: 'Water, waste and microplastics', paragraphs: [
      'A single cotton T-shirt can take around 2,700 litres of water to produce. Synthetic fabrics bring a different problem: every wash sheds tiny plastic fibres that travel through wastewater into rivers and oceans.',
      'Meanwhile, the equivalent of one rubbish truck of textiles is landfilled or burned every second.' ] },
    { heading: 'Who pays the price?', paragraphs: [
      'Most garments are sewn in countries where wages are low and labour protections are weak. The 2013 Rana Plaza collapse in Bangladesh, which killed more than 1,100 garment workers, drew global attention to unsafe factories. Communities near dyeing plants also live with polluted water.' ] },
    { heading: 'What can change?', paragraphs: [
      'Solutions work at several levels. Circular fashion keeps clothes in use longer through repair, resale and recycling. Governments are starting to regulate, with proposals for producer responsibility and limits on destroying unsold stock.',
      'For shoppers, the most effective step is also the simplest: buy less, and wear what you own for longer.' ] },
  ] as ArticleSection[],
}

export const feedbackReport: FeedbackReport = {
  sessionId: 's1',
  topicTitle: 'Fast fashion and its environmental cost',
  date: 'Sep 27, 2026',
  duration: '3:00',
  overallScore: 78,
  verdict: 'Solid talk! Your pacing was excellent.',
  metrics: [
    { key: 'clarity', name: 'Clarity', score: 82, insight: 'Most sentences were clear and well-structured.' },
    { key: 'pace', name: 'Pace', score: 88, value: '142 wpm', insight: 'Right in the ideal range (130–160 wpm).' },
    { key: 'confidence', name: 'Confidence', score: 74, insight: 'Steady voice, slight hesitation at the start.' },
    { key: 'fillers', name: 'Filler words', score: 65, value: '9 fillers', insight: "'um' ×5, 'like' ×4. Try pausing instead." },
    { key: 'eyeContact', name: 'Eye contact', score: 70, insight: 'Looked away from the camera ~30% of the time.' },
    { key: 'relevance', name: 'Relevance', score: 85, insight: 'Covered 4 of 5 key points.' },
    { key: 'vocabulary', name: 'Vocabulary', score: 79, insight: 'Good range; try more topic-specific terms.' },
  ],
  wentWell: [
    'A clear opening that stated your position in the first 15 seconds.',
    'Steady pacing throughout, with natural pauses between points.',
    'A strong close that came back to buying less.',
  ],
  toImprove: [
    "Swap 'um' and 'like' for a short silent pause.",
    'Look at the lens when you land a key point.',
    'Cover labour costs, the one key point you missed.',
  ],
  transcript: [
    { text: 'So, fast fashion is clothing that is designed, made and sold really quickly, and really cheaply. ', isFiller: false },
    { text: 'Um', isFiller: true },
    { text: ', brands release new collections every few weeks, and ', isFiller: false },
    { text: 'like', isFiller: true },
    { text: ', that means we buy more and wear things less. The industry makes over a hundred billion garments a year. ', isFiller: false },
    { text: 'Um', isFiller: true },
    { text: ', a lot of that ends up in landfill. The water footprint is huge too: one T-shirt can take around 2,700 litres. So what can we do? I think the simplest answer is to buy less, and ', isFiller: false },
    { text: 'like', isFiller: true },
    { text: ', actually wear what we already own.', isFiller: false },
  ],
}

export const processingSteps = [
  'Uploaded',
  'Transcribing speech',
  'Analyzing delivery',
  'Generating feedback',
]

export const landing: { heroTitle: string; heroBody: string; features: LandingFeature[]; navLinks: string[] } = {
  heroTitle: 'Master Public Speaking with AI',
  heroBody:
    'SpeakWise gives you a topic, a short reading to prepare, and a camera to practise on. After each talk, AI feedback shows what worked and what to improve.',
  features: [
    { icon: 'shuffle', title: 'Random Speaking Topics', description: 'Fresh prompts across technology, science, business and society, so you never run out of things to talk about.' },
    { icon: 'audio-lines', title: 'AI Speech Analysis', description: 'Scores for clarity, pace, filler words and eye contact after every recording.' },
    { icon: 'book-open', title: 'Vocabulary Improvement', description: 'Read before you speak and pick up topic-specific words you can use right away.' },
    { icon: 'trending-up', title: 'Confidence Tracking', description: 'Watch your scores and streak grow, session by session.' },
  ],
  navLinks: ['Home', 'Features', 'About', 'Contact'],
}

export const historySessions: Session[] = [
  { id: 'h1', topicTitle: 'Fast fashion and its environmental cost', category: 'Environment', durationMin: 3, date: 'Sep 25', score: 78, status: 'completed' },
  { id: 'h2', topicTitle: 'Is social media making us lonelier?', category: 'Society', durationMin: 1, date: 'Sep 23', score: 71, status: 'completed' },
  { id: 'h3', topicTitle: 'The case for a four-day work week', category: 'Business', durationMin: 5, date: 'Sep 20', score: 84, status: 'completed' },
  { id: 'h4', topicTitle: 'Remote work vs. office culture', category: 'Business', durationMin: 3, date: 'Sep 18', score: null, status: 'processing' },
  { id: 'h5', topicTitle: 'Space exploration: worth the cost?', category: 'Science', durationMin: 3, date: 'Sep 15', score: 69, status: 'completed' },
  { id: 'h6', topicTitle: 'Should AI tutors replace homework help?', category: 'Technology', durationMin: 1, date: 'Sep 12', score: 74, status: 'completed' },
  { id: 'h7', topicTitle: 'CRISPR and the ethics of gene editing', category: 'Science', durationMin: 5, date: 'Sep 9', score: 81, status: 'completed' },
  { id: 'h8', topicTitle: 'Is social media making us lonelier?', category: 'Society', durationMin: 3, date: 'Sep 5', score: 66, status: 'completed' },
]
export const historyFilters = ['All', 'Completed', 'In progress'] as const // In progress = status 'processing'
export const historySorts = ['Date', 'Score'] as const

export const defaultPreferences: Preferences = {
  defaultDurationMin: 3,
  readingTextSize: 'Medium',
  selectedCamera: 'FaceTime HD Camera',
  selectedMicrophone: 'MacBook Pro Microphone',
  notifications: true,
}

export const deviceOptions: DeviceOptions = {
  cameras: ['FaceTime HD Camera', 'Logitech C920'],
  microphones: ['MacBook Pro Microphone', 'AirPods Pro', 'Blue Yeti'],
}

// Mock auth: any valid email + password of 6+ chars succeeds after ~900ms; shorter passwords -> wrong-credentials banner.
export const loginCopy = {
  title: 'Welcome back',
  subtitle: 'Practice speaking. Build confidence.',
  brandHeadline: 'Read. Speak. Get better every day.',
  brandBody:
    'Practise short talks on real topics and get AI feedback on clarity, pace and confidence.',
  errors: {
    email: 'Enter a valid email address.',
    password: 'Enter your password.',
    credentials: 'Email or password is incorrect. Check them and try again.',
    inactive: 'Your account is inactive. Contact your administrator.',
  },
}

// ---------- Auth ----------
// Credentials are EMAIL + PASSWORD. Register sets password + confirm password.
export const registerRules = {
  nameRequired: 'Enter your full name.',
  email: 'Enter a valid email address.',
  passwordMin: 8,
  passwordMinMsg: 'Use at least 8 characters.',
  mismatch: "Passwords don't match.",
  // strength: 1 point each -> length>=8; letters+numbers; (uppercase AND symbol) OR length>=12
  strength: {
    1: ['Weak', 'Add more characters and a number.'],
    2: ['Fair', 'Add a capital letter and a symbol, or make it longer.'],
    3: ['Strong', 'Strong password.'],
  } as Record<1 | 2 | 3, [string, string]>,
}

export const mockAccounts: { email: string; password: string; role: Role }[] = [
  { email: 'priya.sharma@example.com', password: 'Speak2026!', role: 'student' },
  { email: 'admin@speakwise.app', password: 'Admin2026!', role: 'admin' },
]

// ---------- Admin ----------
export const adminProfile = { name: 'Admin', firstName: 'Admin', email: 'admin@speakwise.app', initials: 'AD' }
export const adminLastUpdated = 'Sep 27, 2026'

export const adminKpis: AdminKpi[] = [
  { key: 'totalUsers', label: 'Total users', value: 1248, delta: '+64 this month' },
  { key: 'activeUsers', label: 'Active users', value: 890, delta: '71% of all users' },
  { key: 'sessions', label: 'Talk sessions recorded', value: 5630, delta: '+768 this week' },
  { key: 'minutes', label: 'Minutes spoken', value: 14215, delta: '2.5 min per session' },
  { key: 'avgScore', label: 'Average score', value: 74, delta: '+3 vs last month' },
]
export const sessionsPerWeek: WeeklyCount[] = [
  { week: 'Aug 3', count: 420 }, { week: 'Aug 10', count: 468 }, { week: 'Aug 17', count: 455 }, { week: 'Aug 24', count: 512 },
  { week: 'Aug 31', count: 590 }, { week: 'Sep 7', count: 634 }, { week: 'Sep 14', count: 702 }, { week: 'Sep 21', count: 768 },
]
export const sessionsByCategory: CategoryShare[] = [
  { category: 'Technology', pct: 28 }, { category: 'Business', pct: 24 }, { category: 'Society', pct: 19 }, { category: 'Environment', pct: 16 }, { category: 'Science', pct: 13 },
]
export const adminRecentSessions: AdminRecentSession[] = [
  { user: 'Mei Tanaka', topic: 'Space exploration: worth the cost?', score: 81, when: '12 min ago' },
  { user: 'Arjun Mehta', topic: 'The case for a four-day work week', score: 88, when: '40 min ago' },
  { user: 'Priya Sharma', topic: 'Fast fashion and its environmental cost', score: 78, when: '2 h ago' },
  { user: 'Hannah Weber', topic: 'CRISPR and the ethics of gene editing', score: 73, when: '3 h ago' },
  { user: 'Sara Okafor', topic: 'Is social media making us lonelier?', score: 69, when: '5 h ago' },
]
export const adminUsers: AdminUser[] = [
  { id: 'u1', name: 'Priya Sharma', email: 'priya.sharma@example.com', sessions: 12, lastActive: 'Today', joined: 'Aug 02', status: 'Active' },
  { id: 'u2', name: 'Arjun Mehta', email: 'arjun.mehta@example.com', sessions: 27, lastActive: 'Yesterday', joined: 'Jul 14', status: 'Active' },
  { id: 'u3', name: 'Sara Okafor', email: 'sara.okafor@example.com', sessions: 8, lastActive: 'Sep 24', joined: 'Aug 19', status: 'Active' },
  { id: 'u4', name: 'Liam Chen', email: 'liam.chen@example.com', sessions: 3, lastActive: 'Sep 02', joined: 'Aug 28', status: 'Inactive' },
  { id: 'u5', name: 'Mei Tanaka', email: 'mei.tanaka@example.com', sessions: 19, lastActive: 'Sep 26', joined: 'Jun 30', status: 'Active' },
  { id: 'u6', name: 'Diego Alvarez', email: 'diego.alvarez@example.com', sessions: 0, lastActive: 'Never', joined: 'Sep 21', status: 'Inactive' },
  { id: 'u7', name: 'Hannah Weber', email: 'hannah.weber@example.com', sessions: 14, lastActive: 'Sep 25', joined: 'Jul 07', status: 'Active' },
  { id: 'u8', name: 'Omar Haddad', email: 'omar.haddad@example.com', sessions: 6, lastActive: 'Sep 11', joined: 'Aug 09', status: 'Active' },
]
