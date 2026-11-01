import type { SessionPatch } from '@/db/sessions';
import type { Session, Topic } from '@/types/models';

/** Props every session step receives from app/session/[id].tsx. */
export type StepProps = {
  session: Session;
  topic: Topic;
  update: (patch: SessionPatch) => Promise<void>;
  /** The × in the focus header. */
  onClose: () => void;
};
