import type { MantineSize } from '@mantine/core';
import dayjs from 'dayjs';

import {
  useGlobalSettingsState,
  useUserSettingsState
} from '../states/SettingsState';

interface FormatDecmimalOptionsInterface {
  digits?: number;
  minDigits?: number;
  locale?: string;
}

interface FormatCurrencyOptionsInterface {
  digits?: number;
  minDigits?: number;
  currency?: string;
  locale?: string;
  multiplier?: number;
}

export function formatDecimal(
  value: number | null | undefined,
  options: FormatDecmimalOptionsInterface = {}
) {
  const locale = options.locale || navigator.language || 'en-US';

  if (value === null || value === undefined) {
    return value;
  }

  const formatter = new Intl.NumberFormat(locale, {
    style: 'decimal',
    maximumFractionDigits: options.digits ?? 6,
    minimumFractionDigits: options.minDigits ?? 0
  });

  return formatter.format(value);
}

/*
 * format currency (money) value based on current settings
 *
 * Options:
 * - currency: Currency code (uses default value if none provided)
 * - locale: Locale specified (uses default value if none provided)
 * - digits: Maximum number of significant digits (default = 10)
 */
export function formatCurrency(
  value: number | string | null | undefined,
  options: FormatCurrencyOptionsInterface = {}
) {
  if (value == null || value == undefined) {
    return null;
  }

  value = Number.parseFloat(value.toString());

  if (Number.isNaN(value) || !Number.isFinite(value)) {
    return null;
  }

  value *= options.multiplier ?? 1;

  const global_settings = useGlobalSettingsState.getState().lookup;

  let maxDigits = options.digits || global_settings.PRICING_DECIMAL_PLACES || 6;
  maxDigits = Number(maxDigits);
  let minDigits =
    options.minDigits || global_settings.PRICING_DECIMAL_PLACES_MIN || 0;
  minDigits = Number(minDigits);

  // Extract default currency information
  const currency =
    options.currency || global_settings.INVENTREE_DEFAULT_CURRENCY || 'USD';

  // Extract locale information
  const locale = options.locale || navigator.language || 'en-US';

  const formatter = new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currency,
    maximumFractionDigits: Math.max(minDigits, maxDigits),
    minimumFractionDigits: Math.min(minDigits, maxDigits)
  });

  return formatter.format(value);
}

/*
 * Render the price range for the provided values
 */
export function formatPriceRange(
  minValue: number | null,
  maxValue: number | null,
  options: FormatCurrencyOptionsInterface = {}
) {
  // If neither values are provided, return a dash
  if (minValue == null && maxValue == null) {
    return '-';
  }

  if (minValue == null) {
    return formatCurrency(maxValue!, options);
  }

  if (maxValue == null) {
    return formatCurrency(minValue!, options);
  }

  // If both values are the same, return a single value
  if (minValue == maxValue) {
    return formatCurrency(minValue, options);
  }

  // Otherwise, return a range
  return `${formatCurrency(minValue, options)} - ${formatCurrency(
    maxValue,
    options
  )}`;
}

/*
 * Format a file size (in bytes) into a human-readable format
 */
export function formatFileSize(size: number) {
  const suffixes: string[] = ['B', 'KB', 'MB', 'GB'];

  let idx = 0;

  while (size > 1024 && idx < suffixes.length) {
    size /= 1024;
    idx++;
  }

  return `${size.toFixed(2)} ${suffixes[idx]}`;
}

interface FormatDateOptionsInterface {
  showTime?: boolean;
  showSeconds?: boolean;
}

/*
 * Render the provided date in the user-specified format.
 *
 * The provided "date" variable is a string, nominally ISO format e.g. 2022-02-22
 * The user-configured setting DATE_DISPLAY_FORMAT determines how the date should be displayed.
 */
export function formatDate(
  date: string,
  options: FormatDateOptionsInterface = {}
) {
  if (!date) {
    return '-';
  }

  const user_settings = useUserSettingsState.getState().lookup;
  let fmt = user_settings.DATE_DISPLAY_FORMAT || 'YYYY-MM-DD';

  if (options.showTime) {
    fmt += ' HH:mm';
    if (options.showSeconds) {
      fmt += ':ss';
    }
  }

  const m = dayjs(date);

  if (m.isValid()) {
    return m.format(fmt);
  } else {
    // Invalid input string, simply return provided value
    return date;
  }
}

export type UiSizeType = MantineSize | string | number;
