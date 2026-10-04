import { useNavigate } from 'react-router'
import { ROUTES } from '@/app/routes'
import { FocusLayout } from '@/components/layout/FocusLayout'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { topicService } from '@/core/services'
import { formatClock } from '@/core/utils'
import { useIsDesktop } from '@/hooks/useMediaQuery'
import { RecordDesktop } from './RecordDesktop'
import { RecordMobile } from './RecordMobile'
import { useRecordSession } from './useRecordSession'

export function RecordPage() {
  const navigate = useNavigate()
  const isDesktop = useIsDesktop()
  const rec = useRecordSession()
  const keyPoints = topicService.getKeyPoints()
  const exit = () => navigate(ROUTES.home)

  return (
    <FocusLayout step="Record" tone="dark" fitViewport hideMobileTopBar onExit={exit}>
      {isDesktop ? (
        <RecordDesktop rec={rec} keyPoints={keyPoints} />
      ) : (
        <RecordMobile rec={rec} keyPoints={keyPoints} onExit={exit} />
      )}

      <ConfirmDialog
        open={rec.endDialogOpen}
        title="End early?"
        body={`You have ${formatClock(rec.remainingSec)} left. Your recording so far will be kept for review.`}
        confirmLabel="End recording"
        cancelLabel="Keep talking"
        danger
        scrim="dark"
        onConfirm={rec.endNow}
        onCancel={rec.keepTalking}
      />
    </FocusLayout>
  )
}
