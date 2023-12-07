// dec2hex :: Integer -> String
// i.e. 0-255 -> '00'-'ff'
function dec2hex(dec: number) {
  return dec.toString(16).padStart(2, '0');
}

/**
 * Generate a unique ID string with the specified number of values
 */
export function generateUniqueId(length: number = 8): string {
  let arr = new Uint8Array(length / 2);
  window.crypto.getRandomValues(arr);

  return Array.from(arr, dec2hex).join('');
}
