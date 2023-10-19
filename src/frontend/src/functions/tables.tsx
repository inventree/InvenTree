/**
 * Reduce an input string to a given length, adding an ellipsis if necessary
 * @param str - String to shorten
 * @param len - Length to shorten to
 */
export function shortenString({
  str,
  len = 100
}: {
  str: string | undefined;
  len?: number;
}) {
  // Ensure that the string is a string
  str = str ?? '';
  str = str.toString();

  // If the string is already short enough, return it
  if (str.length <= len) {
    return str;
  }

  // Otherwise, shorten it
  let N = Math.floor(len / 2 - 1);

  return str.slice(0, N) + '...' + str.slice(-N);
}
