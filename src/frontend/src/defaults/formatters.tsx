import dayjs from 'dayjs';

import {
  type FormatCurrencyOptionsInterface,
  formatCurrencyValue
} from '@lib/functions/Formatting';
import {
  useGlobalSettingsState,
  useUserSettingsState
} from '../states/SettingsStates';

export { formatDecimal, formatFileSize } from '@lib/functions/Formatting';

/**
 * Format currency value, automatically localized based on user settings.
 */
export function formatCurrency(
  value: number | string | null | undefined,
  options: FormatCurrencyOptionsInterface = {
    digits: 6,
    minDigits: 0,
    currency: 'USD',
    multiplier: 1
  }
) {
  const global_settings = useGlobalSettingsState.getState().lookup;

  // Extract default digit formatting
  options.digits =
    options?.digits ?? Number(global_settings.PRICING_DECIMAL_PLACES) ?? 6;
  options.minDigits =
    options?.minDigits ??
    Number(global_settings.PRICING_DECIMAL_PLACES_MIN) ??
    0;

  options.currency =
    options?.currency ?? (global_settings.INVENTREE_DEFAULT_CURRENCY || 'USD');

  return formatCurrencyValue(value, options);
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
