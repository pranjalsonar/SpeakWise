// SpeakWise dummy data, from design_handoff_speakwise/mockData.ts.
// Only src/core/services may import this file. Screens get data through services.
import type {
  CategoryFilter,
  DeviceOptions,
  FeedbackReport,
  LandingFeature,
  Preferences,
  Role,
  Session,
  Stats,
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

export const ownTopicExamples = [
  // Topics Wikipedia covers well (own topics are resolved against Wikipedia).
  'Is chess a sport?',
  'Why cities should ban cars',
  'Should schools start later in the morning?',
]

export const recentSessions: Session[] = [
  { id: 's1', topicTitle: 'Fast fashion and its environmental cost', category: 'Environment', durationMin: 3, date: 'Sep 25', score: 78, status: 'completed' },
  { id: 's2', topicTitle: 'Is social media making us lonelier?', category: 'Society', durationMin: 1, date: 'Sep 23', score: 71, status: 'completed' },
  { id: 's3', topicTitle: 'The case for a four-day work week', category: 'Business', durationMin: 5, date: 'Sep 20', score: 84, status: 'completed' },
  { id: 's4', topicTitle: 'Remote work vs. office culture', category: 'Business', durationMin: 3, date: 'Sep 18', score: null, status: 'processing' },
]

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
]
