import { useSQLiteContext } from 'expo-sqlite';
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';

import { getProfile, saveProfile as saveProfileRow } from '@/db/profile';
import type { Profile, ProfileInput } from '@/types/models';

type ProfileContextValue = {
  profile: Profile | null;
  loading: boolean;
  saveProfile: (input: ProfileInput) => Promise<void>;
};

const ProfileContext = createContext<ProfileContextValue | null>(null);

export function ProfileProvider({ children }: { children: ReactNode }) {
  const db = useSQLiteContext();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getProfile(db)
      .then(setProfile)
      .finally(() => setLoading(false));
  }, [db]);

  const saveProfile = useCallback(
    async (input: ProfileInput) => {
      await saveProfileRow(db, input);
      setProfile(await getProfile(db));
    },
    [db]
  );

  return (
    <ProfileContext.Provider value={{ profile, loading, saveProfile }}>{children}</ProfileContext.Provider>
  );
}

export function useProfile() {
  const ctx = useContext(ProfileContext);
  if (!ctx) throw new Error('useProfile must be used inside <ProfileProvider>');
  return ctx;
}
