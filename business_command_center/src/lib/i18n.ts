'use client';

import { useState, useCallback } from 'react';
import localesData from '@/locales_ui.json';

export type SupportedLocale = 'en' | 'es' | 'pt' | 'fr' | 'de' | 'it' | 'ja';

export const SUPPORTED_LOCALES: readonly SupportedLocale[] = [
  'en',
  'es',
  'pt',
  'fr',
  'de',
  'it',
  'ja',
] as const;

export const LOCALE_LABELS: Record<SupportedLocale, { label: string; flag: string }> = {
  en: { label: 'English', flag: '🇬🇧' },
  es: { label: 'Español', flag: '🇪🇸' },
  pt: { label: 'Português', flag: '🇧🇷' },
  fr: { label: 'Français', flag: '🇫🇷' },
  de: { label: 'Deutsch', flag: '🇩🇪' },
  it: { label: 'Italiano', flag: '🇮🇹' },
  ja: { label: '日本語', flag: '🇯🇵' },
};

export type TranslationKey = keyof typeof localesData.en;

/**
 * Pure translation lookup with cascaded fallback:
 * requestedLocale[key] -> englishFallback[key] -> key
 */
export function translate(
  key: TranslationKey,
  locale: SupportedLocale = 'en',
  params?: Record<string, string | number>
): string {
  const dictionary =
    (localesData as Record<SupportedLocale, Record<string, string>>)[locale] ||
    localesData.en;
  let text = dictionary[key] || localesData.en[key] || String(key);

  if (params) {
    for (const [paramKey, paramVal] of Object.entries(params)) {
      text = text.replace(new RegExp(`\\{${paramKey}\\}`, 'g'), String(paramVal));
    }
  }

  return text;
}

/**
 * Format currency with native ECMA-402 Intl.NumberFormat according to regional convention.
 */
export function formatCurrency(
  amount: number,
  currencyCode: string = 'EUR',
  locale: SupportedLocale = 'en'
): string {
  const cleanCode = currencyCode.split(' ')[0].replace(/[^A-Z]/g, '') || 'EUR';
  const localeTag =
    locale === 'en'
      ? 'en-US'
      : locale === 'es'
      ? 'es-ES'
      : locale === 'pt'
      ? 'pt-BR'
      : locale === 'fr'
      ? 'fr-FR'
      : locale === 'de'
      ? 'de-DE'
      : locale === 'it'
      ? 'it-IT'
      : 'ja-JP';

  try {
    return new Intl.NumberFormat(localeTag, {
      style: 'currency',
      currency: cleanCode,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    return `${cleanCode} ${amount.toFixed(2)}`;
  }
}

/**
 * Format date with native ECMA-402 Intl.DateTimeFormat according to regional convention.
 */
export function formatDate(
  date: Date | string | number,
  locale: SupportedLocale = 'en',
  options: Intl.DateTimeFormatOptions = { dateStyle: 'medium' }
): string {
  const d = typeof date === 'string' || typeof date === 'number' ? new Date(date) : date;
  const localeTag =
    locale === 'en'
      ? 'en-GB'
      : locale === 'es'
      ? 'es-ES'
      : locale === 'pt'
      ? 'pt-BR'
      : locale === 'fr'
      ? 'fr-FR'
      : locale === 'de'
      ? 'de-DE'
      : locale === 'it'
      ? 'it-IT'
      : 'ja-JP';

  try {
    return new Intl.DateTimeFormat(localeTag, options).format(d);
  } catch {
    return d.toLocaleDateString();
  }
}

const LOCALE_COOKIE_NAME = 'assessment_locale';

/**
 * React Hook for component translation and locale switching.
 */
export function useTranslation(defaultLocale: SupportedLocale = 'en') {
  const [locale, setLocaleState] = useState<SupportedLocale>(() => {
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem(LOCALE_COOKIE_NAME) as SupportedLocale | null;
        if (saved && SUPPORTED_LOCALES.includes(saved)) {
          return saved;
        }

        const navLang = navigator.language?.slice(0, 2) as SupportedLocale;
        if (navLang && SUPPORTED_LOCALES.includes(navLang)) {
          return navLang;
        }
      } catch {
        // Fallback
      }
    }
    return defaultLocale;
  });

  const changeLocale = useCallback((newLocale: SupportedLocale) => {
    setLocaleState(newLocale);
    try {
      localStorage.setItem(LOCALE_COOKIE_NAME, newLocale);
      document.cookie = `${LOCALE_COOKIE_NAME}=${newLocale}; path=/; max-age=31536000; SameSite=Lax`;
    } catch {}
  }, []);

  const t = useCallback(
    (key: TranslationKey, params?: Record<string, string | number>) => {
      return translate(key, locale, params);
    },
    [locale]
  );

  return {
    locale,
    changeLocale,
    t,
    formatCurrency: (amount: number, currency?: string) =>
      formatCurrency(amount, currency, locale),
    formatDate: (date: Date | string | number, options?: Intl.DateTimeFormatOptions) =>
      formatDate(date, locale, options),
  };
}
