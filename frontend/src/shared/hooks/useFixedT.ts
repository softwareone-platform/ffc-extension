import { useTranslation } from 'react-i18next';

export function useFixedT(keyPrefix: string) {
  return useTranslation(undefined, { keyPrefix }).t;
}
