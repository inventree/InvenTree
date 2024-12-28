import { t } from '@lingui/macro';

/**
 * Extract a sensible error message from an API error response
 * @param error The error response from the API
 * @param field The field to extract the error message from (optional)
 * @param defaultMessage A default message to use if no error message is found (optional)
 */
export function extractErrorMessage({
  error,
  field,
  defaultMessage
}: {
  error: any;
  field?: string;
  defaultMessage?: string;
}): string {
  const error_data = error.response?.data ?? null;

  let message = '';

  if (error_data) {
    message = error_data[field ?? 'error'] ?? error_data['non_field_errors'];
  }

  // No message? Look at the response status codes
  if (!message) {
    const status = error.response?.status ?? null;

    if (status) {
      switch (status) {
        case 400:
          message = t`Bad request`;
          break;
        case 401:
          message = t`Unauthorized`;
          break;
        case 403:
          message = t`Forbidden`;
          break;
        case 404:
          message = t`Not found`;
          break;
        case 405:
          message = t`Method not allowed`;
          break;
        case 500:
          message = t`Internal server error`;
          break;
        default:
          break;
      }
    }
  }

  if (!message) {
    message = defaultMessage ?? t`An error occurred`;
  }

  return message;
}
