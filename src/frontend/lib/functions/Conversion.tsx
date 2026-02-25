/*
 * Determine if the provided value is "true":
 *
 * Many settings stored on the server are true/false,
 * but stored as string values, "true" / "false".
 *
 * This function provides a wrapper to ensure that the return type is boolean
 */
export function isTrue(value: any): boolean {
  if (value === true) {
    return true;
  }

  if (value === false) {
    return false;
  }

  const s = String(value).trim().toLowerCase();

  return ['true', 'yes', '1', 'on', 't', 'y'].includes(s);
}

/*
 * Resolve a nested item in an object.
 * Returns the resolved item, if it exists.
 *
 * e.g. resolveItem(data, "sub.key.accessor")
 *
 * Allows for retrieval of nested items in an object.
 */
export function resolveItem(obj: any, path: string): any {
  // Return the top-level object if no path is provided
  if (path == null || path === '') {
    return obj;
  }

  const properties = path.split('.');
  return properties.reduce((prev, curr) => prev?.[curr], obj);
}

export function identifierString(value: string): string {
  // Convert an input string e.g. "Hello World" into a string that can be used as an identifier, e.g. "hello-world"

  value = value || '-';

  return value.toLowerCase().replace(/[^a-z0-9]/g, '-');
}

export function toNumber(
  value: any,
  defaultValue: number | null = 0
): number | null {
  // Convert the provided value into a number (if possible)

  if (value == undefined || value == null || value === '') {
    return defaultValue;
  }

  // Case 1: numeric already
  if (typeof value === 'number') return value;

  // Case 2: react-number-format object
  if (typeof value === 'object') {
    if ('floatValue' in value && typeof value.floatValue === 'number') {
      return value.floatValue;
    }
    if ('value' in value) {
      const parsed = Number(value.value);
      return Number.isNaN(parsed) ? Number.NaN : parsed;
    }
  }

  // Case 3: string
  if (typeof value === 'string') {
    const parsed = Number(value);
    return Number.isNaN(parsed) ? Number.NaN : parsed;
  }

  return Number.NaN;
}
