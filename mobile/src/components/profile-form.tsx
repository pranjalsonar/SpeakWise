import { useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { Button } from '@/components/ui/button';
import { Chip } from '@/components/ui/chip';
import { TextField } from '@/components/ui/text-field';
import { GENDERS, GOALS } from '@/constants/profile';
import { Spacing } from '@/constants/theme';
import type { Profile, ProfileInput } from '@/types/models';
import { validateProfile, type ProfileErrors, type ProfileFormValues } from '@/utils/profile-validation';

type ProfileFormProps = {
  initial?: Profile | null;
  submitLabel: string;
  onSubmit: (profile: ProfileInput) => Promise<void>;
  onCancel?: () => void;
};

export function ProfileForm({ initial, submitLabel, onSubmit, onCancel }: ProfileFormProps) {
  const [values, setValues] = useState<ProfileFormValues>({
    firstName: initial?.firstName ?? '',
    lastName: initial?.lastName ?? '',
    age: initial?.age != null ? String(initial.age) : '',
    gender: initial?.gender ?? null,
    goal: initial?.goal ?? null,
  });
  const [errors, setErrors] = useState<ProfileErrors>({});
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const set = <K extends keyof ProfileFormValues>(key: K, value: ProfileFormValues[K]) => {
    setValues((v) => ({ ...v, [key]: value }));
    if (key in errors) setErrors((e) => ({ ...e, [key]: undefined }));
  };

  const submit = async () => {
    const result = validateProfile(values);
    setErrors(result.errors);
    if (!result.profile) return;
    setSaving(true);
    setSaveError(null);
    try {
      await onSubmit(result.profile);
    } catch {
      setSaveError('Could not save your profile. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <View style={styles.form}>
      <TextField
        label="First name"
        value={values.firstName}
        onChangeText={(t) => set('firstName', t)}
        error={errors.firstName}
        placeholder="e.g. Raj"
        autoCapitalize="words"
        autoComplete="given-name"
        textContentType="givenName"
        returnKeyType="next"
      />
      <TextField
        label="Last name"
        optional
        value={values.lastName}
        onChangeText={(t) => set('lastName', t)}
        error={errors.lastName}
        placeholder="e.g. Patil"
        autoCapitalize="words"
        autoComplete="family-name"
        textContentType="familyName"
      />
      <TextField
        label="Age"
        optional
        value={values.age}
        onChangeText={(t) => set('age', t.replace(/[^0-9]/g, '').slice(0, 3))}
        error={errors.age}
        placeholder="e.g. 21"
        keyboardType="number-pad"
        maxLength={3}
      />

      <View style={styles.group}>
        <ThemedText type="smallBold">
          Gender <ThemedText type="small" themeColor="textSecondary">(optional)</ThemedText>
        </ThemedText>
        <View style={styles.chips}>
          {GENDERS.map((g) => (
            <Chip
              key={g}
              label={g}
              selected={values.gender === g}
              onPress={() => set('gender', values.gender === g ? null : g)}
            />
          ))}
        </View>
      </View>

      <View style={styles.group}>
        <ThemedText type="smallBold">
          What do you want to get better at?{' '}
          <ThemedText type="small" themeColor="textSecondary">(optional)</ThemedText>
        </ThemedText>
        <View style={styles.chips}>
          {GOALS.map((g) => (
            <Chip
              key={g}
              label={g}
              selected={values.goal === g}
              onPress={() => set('goal', values.goal === g ? null : g)}
            />
          ))}
        </View>
      </View>

      {saveError ? (
        <ThemedText type="small" themeColor="danger">
          {saveError}
        </ThemedText>
      ) : null}

      <View style={styles.actions}>
        <Button title={submitLabel} onPress={submit} loading={saving} />
        {onCancel ? <Button title="Cancel" variant="ghost" onPress={onCancel} disabled={saving} /> : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  form: {
    gap: Spacing.three + 4,
  },
  group: {
    gap: Spacing.two,
  },
  chips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.two,
  },
  actions: {
    gap: Spacing.two,
    marginTop: Spacing.two,
  },
});
