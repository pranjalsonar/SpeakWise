import { Mic } from 'lucide-react'
import { Link } from 'react-router'
import { ROUTES } from '@/app/routes'
import { AppShell } from '@/components/layout/AppShell'
import { SessionRow } from '@/components/shared/SessionRow'
import { EmptyState } from '@/components/ui/EmptyState'
import { Skeleton } from '@/components/ui/Skeleton'
import { useCurrentUser } from '@/context/AuthContext'
import { useAsync } from '@/core/hooks/useAsync'
import { sessionService, topicService } from '@/core/services'
import { greetingFor } from '@/core/utils'
import { useStartSession } from '@/hooks/useStartSession'
import { StartSessionCard } from './StartSessionCard'
import { StatsRow } from './StatsRow'
import { TodayTopicCard } from './TodayTopicCard'
import './HomePage.css'

export function HomePage() {
  const user = useCurrentUser()
  const startSession = useStartSession()
  const { data, loading } = useAsync(() => sessionService.getDashboard(user.email), [user.email])
  const todaysTopic = topicService.getTodaysTopic()
  const hasSessions = (data?.recentSessions.length ?? 0) > 0

  return (
    <AppShell>
      <div className="home-page">
        <header className="home-page__greeting">
          <h1 className="home-page__title">
            {greetingFor(new Date())}, {user.firstName} 👋
          </h1>
          <p className="home-page__subtitle">Ready for today's talk?</p>
        </header>

        <div className="home-page__hero">
          <div className="home-page__start">
            <StartSessionCard
              onStart={() => startSession()}
              onSuggest={() => startSession({ random: true })}
            />
          </div>
          <div className="home-page__today">
            <TodayTopicCard
              topic={todaysTopic}
              onUse={() => startSession({ topicId: todaysTopic.id })}
            />
          </div>
        </div>

        {loading && (
          <div className="home-page__stats">
            <Skeleton height={96} radius={32} />
          </div>
        )}

        {!loading && data && hasSessions && (
          <>
            <div className="home-page__stats">
              <StatsRow stats={data.stats} />
            </div>
            <section className="home-page__recent" aria-labelledby="recent-title">
              <div className="home-page__recent-head">
                <h2 id="recent-title" className="home-page__recent-title">
                  Recent sessions
                </h2>
                <Link to={ROUTES.history} className="text-link home-page__view-all">
                  View all
                </Link>
              </div>
              <div className="home-page__recent-list">
                {data.recentSessions.map((session) => (
                  <SessionRow key={session.id} session={session} />
                ))}
              </div>
            </section>
          </>
        )}

        {!loading && !hasSessions && (
          <div className="home-page__empty">
            <EmptyState
              icon={<Mic />}
              title="No sessions yet"
              body="Your first talk takes about 20 minutes: 15 to read, a few to speak. Your scores, minutes and streak will show up here."
            />
          </div>
        )}
      </div>
    </AppShell>
  )
}
