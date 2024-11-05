import { t } from '@lingui/macro';

import GenericErrorPage from './GenericErrorPage';
import NotAuthenticated from './NotAuthenticated';
import NotFound from './NotFound';
import PermissionDenied from './PermissionDenied';

export default function ClientError({ status }: Readonly<{ status?: number }>) {
  switch (status) {
    case 401:
      return <NotAuthenticated />;
    case 403:
      return <PermissionDenied />;
    case 404:
      return <NotFound />;
    default:
      break;
  }

  // Generic client error
  return (
    <GenericErrorPage
      title={t`Client Error`}
      message={t`Client error occurred`}
      status={status}
    />
  );
}
