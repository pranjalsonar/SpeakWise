import type { Report } from '@/types/report';

export type Category =
  | 'Science'
  | 'Space'
  | 'History'
  | 'Current Affairs'
  | 'Literature'
  | 'Fiction & Myth';

export type Profile = {
  firstName: string;
  lastName: string | null;
  age: number | null;
  gender: string | null;
  goal: string | null;
  createdAt: number;
};

export type ProfileInput = Omit<Profile, 'createdAt'>;

export type Topic = {
  id: string;
  title: string;
  category: Category;
  level: string;
  readMinutes: number;
  summary: string;
  talkingPoints: string[];
  body: string;
  wordCount: number;
  asOf: string | null;
};

export type TopicListItem = Pick<Topic, 'id' | 'title' | 'category' | 'readMinutes' | 'summary'>;

/** Session lifecycle; every change is persisted so the app can resume after being closed. */
export type SessionStage =
  | 'reading'
  | 'choosing_duration'
  | 'ready_to_record'
  | 'recorded'
  | 'uploading'
  | 'analyzing'
  | 'done'
  | 'failed'
  | 'abandoned';

export type Session = {
  id: number;
  topicId: string;
  stage: SessionStage;
  durationSec: number | null;
  readingProgress: number;
  videoPath: string | null;
  jobId: string | null;
  report: Report | null;
  overallScore: number | null;
  error: string | null;
  createdAt: number;
  updatedAt: number;
};

/** Shape of src/content/articles.json (also read by the backend for the LLM judge). */
export type ArticlesFile = {
  version: number;
  articles: {
    id: string;
    title: string;
    category: Category;
    level: string;
    word_count: number;
    read_minutes: number;
    summary: string;
    talking_points: string[];
    body: string;
    as_of?: string | null;
  }[];
};
