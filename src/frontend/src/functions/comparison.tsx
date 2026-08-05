/** Generic value-comparison helpers, used to keep memoized props/state stable */

function isReactElement(value: any): boolean {
  return (
    value != null &&
    typeof value === 'object' &&
    (value.$$typeof === Symbol.for('react.element') ||
      value.$$typeof === Symbol.for('react.transitional.element'))
  );
}

/**
 * Recursively compare two values for structural equivalence.
 *
 * Useful when comparing generated data (e.g. field definitions rebuilt by a
 * `useMemo`, or table row data) that may get a fresh object/array/JSX-element
 * reference on every recompute even though nothing meaningful changed -
 * without this, every consumer downstream would be treated as "changed" and
 * re-render unnecessarily.
 *
 * Functions are deliberately compared by reference only - unlike a JSX icon,
 * a callback's behavior can depend on values it closes over, so we can't
 * assume two function instances are interchangeable.
 */
export function isEquivalent(a: any, b: any): boolean {
  if (Object.is(a, b)) {
    return true;
  }

  if (isReactElement(a) && isReactElement(b)) {
    return a.type === b.type && isEquivalent(a.props, b.props);
  }

  if (typeof a === 'function' || typeof b === 'function') {
    return false;
  }

  if (Array.isArray(a) || Array.isArray(b)) {
    if (!Array.isArray(a) || !Array.isArray(b) || a.length !== b.length) {
      return false;
    }
    return a.every((item, idx) => isEquivalent(item, b[idx]));
  }

  if (a && b && typeof a === 'object' && typeof b === 'object') {
    const aKeys = Object.keys(a);
    const bKeys = Object.keys(b);
    if (aKeys.length !== bKeys.length) {
      return false;
    }
    return aKeys.every((key) => isEquivalent(a[key], b[key]));
  }

  return false;
}
