import { reactive, ref } from 'vue';

export interface ValidationRule {
  validate: (value: string) => boolean;
  message: string;
}

export interface FieldConfig {
  rules?: ValidationRule[];
}

export interface FormConfig {
  [key: string]: FieldConfig;
}

export function useFormValidation<T extends Record<string, string>>(
  initialValues: T,
  config: FormConfig = {}
) {
  const form = reactive({ ...initialValues }) as T;
  const errors = reactive<Record<keyof T, string>>(
    Object.keys(initialValues).reduce(
      (acc, key) => ({ ...acc, [key]: '' }),
      {} as Record<keyof T, string>
    )
  );
  const generalError = ref('');

  function clearErrors() {
    Object.keys(errors).forEach((key) => {
      (errors as Record<string, string>)[key] = '';
    });
    generalError.value = '';
  }

  function setError(field: keyof T, message: string) {
    (errors as Record<string, string>)[field as string] = message;
  }

  function setGeneralError(message: string) {
    generalError.value = message;
  }

  function validate(): boolean {
    clearErrors();
    let isValid = true;

    for (const [field, fieldConfig] of Object.entries(config)) {
      const value = (form as Record<string, string>)[field] || '';
      const rules = fieldConfig.rules || [];

      for (const rule of rules) {
        if (!rule.validate(value)) {
          setError(field as keyof T, rule.message);
          isValid = false;
          break;
        }
      }
    }

    return isValid;
  }

  function reset() {
    Object.keys(initialValues).forEach((key) => {
      (form as Record<string, string>)[key] = initialValues[key as keyof T] ?? '';
    });
    clearErrors();
  }

  return {
    form,
    errors,
    generalError,
    validate,
    setError,
    setGeneralError,
    clearErrors,
    reset,
  };
}

// Common validation rules
export const rules = {
  required: (message = 'Обязательное поле'): ValidationRule => ({
    validate: (value) => value.trim().length > 0,
    message,
  }),

  minLength: (min: number, message?: string): ValidationRule => ({
    validate: (value) => value.length >= min,
    message: message || `Минимум ${min} символов`,
  }),

  maxLength: (max: number, message?: string): ValidationRule => ({
    validate: (value) => value.length <= max,
    message: message || `Максимум ${max} символов`,
  }),

  email: (message = 'Некорректный email'): ValidationRule => ({
    validate: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
    message,
  }),

  alphanumeric: (message = 'Только буквы, цифры и _'): ValidationRule => ({
    validate: (value) => /^[a-zA-Z0-9_]+$/.test(value),
    message,
  }),

  password: (message = 'Минимум 8 символов, буквы и цифры'): ValidationRule => ({
    validate: (value) => value.length >= 8 && /[a-zA-Z]/.test(value) && /\d/.test(value),
    message,
  }),
};
