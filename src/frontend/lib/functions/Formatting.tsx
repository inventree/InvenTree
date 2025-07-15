export interface FormatDecmimalOptionsInterface {
  digits?: number;
  minDigits?: number;
  locale?: string;
}

export interface FormatCurrencyOptionsInterface {
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

  try {
    const formatter = new Intl.NumberFormat(locale, {
      style: 'decimal',
      maximumFractionDigits: options.digits ?? 6,
      minimumFractionDigits: options.minDigits ?? 0
    });

    return formatter.format(value);
  } catch (e) {
    console.error('Error formatting decimal:', e);
    // Return the unformatted value if formatting fails
    return value;
  }
}

/*
 * format currency (money) value based on current settings
 *
 * Options:
 * - currency: Currency code (uses default value if none provided)
 * - locale: Locale specified (uses default value if none provided)
 * - digits: Maximum number of significant digits (default = 10)
 */
export function formatCurrencyValue(
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

  // Extract locale information
  const locale = options.locale || navigator.language || 'en-US';

  const minDigits = options.minDigits ?? 0;
  const maxDigits = options.digits ?? 6;

  try {
    const formatter = new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: options.currency || 'USD',
      maximumFractionDigits: Math.max(minDigits, maxDigits),
      minimumFractionDigits: Math.min(minDigits, maxDigits)
    });

    return formatter.format(value);
  } catch (e) {
    console.error('Error formatting currency:', e);
    // Return the unformatted value if formatting fails
    return value;
  }
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
