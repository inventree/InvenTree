// Various helper functions

export { apiUrl, extractErrorMessage } from './functions/api';
export { cancelEvent } from './functions/events';
export { identifierString, isTrue } from './functions/conversion';
export { shortenString } from './functions/conversion';

export {
  invalidResponse,
  permissionDenied,
  showApiErrorMessage,
  showLoginNotification,
  showTimeoutNotification
} from './functions/notifications';

export {
  formatDecimal,
  formatCurrency,
  formatPriceRange,
  formatFileSize,
  formatDate
} from './functions/formatting';

export {
  constructField,
  constructFormUrl,
  extractAvailableFields,
  mapFields
} from './functions/forms';

export {
  generateUrl,
  getBaseUrl,
  getDetailUrl,
  navigateToLink
} from './functions/navigation';
