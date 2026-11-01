import { AGE_MAX, AGE_MIN, NAME_MAX_LENGTH } from '@/constants/profile';
import type { ProfileInput } from '@/types/models';

export type ProfileFormValues = {
  firstName: string;
  lastName: string;
  age: string;
  gender: string | null;
  goal: string | null;
};

export type ProfileErrors = Partial<Record<'firstName' | 'lastName' | 'age', string>>;

const INVALID_NAME_CHARS = /[0-9!@#$%^&*()_+=[\]{};:"\\|,<>/?~`]/;

function validateName(value: string, label: string, required: boolean): string | undefined {
  const name = value.trim();
  if (!name) return required ? `Please enter your ${label}.` : undefined;
  if (name.length > NAME_MAX_LENGTH) return `${label[0].toUpperCase()}${label.slice(1)} is too long.`;
  if (INVALID_NAME_CHARS.test(name)) return 'Use letters only (spaces, - and \' are fine).';
  return undefined;
}

/** Returns field errors, or the cleaned profile when everything is valid. */
export function validateProfile(values: ProfileFormValues): { errors: ProfileErrors; profile?: ProfileInput } {
  const errors: ProfileErrors = {};
  errors.firstName = validateName(values.firstName, 'first name', true);
  errors.lastName = validateName(values.lastName, 'last name', false);

  let age: number | null = null;
  if (values.age.trim()) {
    age = Number(values.age.trim());
    if (!Number.isInteger(age) || age < AGE_MIN || age > AGE_MAX) {
      errors.age = `Enter an age between ${AGE_MIN} and ${AGE_MAX}.`;
    }
  }

  const clean = Object.fromEntries(Object.entries(errors).filter(([, v]) => v)) as ProfileErrors;
  if (Object.keys(clean).length) return { errors: clean };

  return {
    errors: {},
    profile: {
      firstName: values.firstName.trim().replace(/\s+/g, ' '),
      lastName: values.lastName.trim().replace(/\s+/g, ' ') || null,
      age,
      gender: values.gender,
      goal: values.goal,
    },
  };
}
