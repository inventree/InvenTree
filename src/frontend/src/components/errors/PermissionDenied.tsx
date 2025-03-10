import { t } from '@lingui/macro';

import GenericErrorPage from './GenericErrorPage';

export default function PermissionDenied() {
  return (
    <GenericErrorPage
      title={t`Permission Denied`}
      message={t`You do not have permission to view this page.`}
    />
  );
}
