import type { MaterialIcons } from '@expo/vector-icons';
import type { ComponentProps } from 'react';

import type { Category } from '@/types/models';

export const CATEGORIES: { name: Category; icon: ComponentProps<typeof MaterialIcons>['name'] }[] = [
  { name: 'Science', icon: 'science' },
  { name: 'Space', icon: 'rocket-launch' },
  { name: 'History', icon: 'account-balance' },
  { name: 'Current Affairs', icon: 'public' },
  { name: 'Literature', icon: 'auto-stories' },
  { name: 'Fiction & Myth', icon: 'auto-awesome' },
];

export const categoryIcon = (c: Category) => CATEGORIES.find((x) => x.name === c)?.icon ?? 'article';
