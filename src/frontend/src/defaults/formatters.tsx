import dayjs from 'dayjs';

import {
  useGlobalSettingsState,
  useUserSettingsState
} from '../states/SettingsState';

interface formatCurrencyOptionsType {
  digits?: number;
  minDigits?: number;
  currency?: string;
  locale?: string;
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
  value: number | null,
  options: formatCurrencyOptionsType = {}
) {
  if (value == null) {
    return null;
  }

  const global_settings = useGlobalSettingsState.getState().lookup;

  let maxDigits = options.digits || global_settings.PRICING_DECIMAL_PLACES || 6;
  maxDigits = Number(maxDigits);
  let minDigits =
    options.minDigits || global_settings.PRICING_DECIMAL_PLACES_MIN || 0;
  minDigits = Number(minDigits);

  // Extract default currency information
  let currency =
    options.currency || global_settings.INVENTREE_DEFAULT_CURRENCY || 'USD';

  // Extract locale information
  let locale = options.locale || navigator.language || 'en-US';

  let formatter = new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currency,
    maximumFractionDigits: maxDigits,
    minimumFractionDigits: minDigits
  });

  return formatter.format(value);
}

/*
 * Render the price range for the provided values
 */
export function formatPriceRange(
  minValue: number | null,
  maxValue: number | null,
  options: formatCurrencyOptionsType = {}
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

interface renderDateOptionsType {
  showTime?: boolean;
}

/*
 * Render the provided date in the user-specified format.
 *
 * The provided "date" variable is a string, nominally ISO format e.g. 2022-02-22
 * The user-configured setting DATE_DISPLAY_FORMAT determines how the date should be displayed.
 */
export function renderDate(date: string, options: renderDateOptionsType = {}) {
  if (!date) {
    return '-';
  }

  const user_settings = useUserSettingsState.getState().lookup;
  let fmt = user_settings.DATE_DISPLAY_FORMAT || 'YYYY-MM-DD';

  if (options.showTime) {
    fmt += ' HH:mm';
  }

  const m = dayjs(date);

  if (m.isValid()) {
    return m.format(fmt);
  } else {
    // Invalid input string, simply return provided value
    return date;
  }
}
