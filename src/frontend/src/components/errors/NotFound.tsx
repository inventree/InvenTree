import { t } from '@lingui/macro';

import GenericErrorPage from './GenericErrorPage';

export default function NotFound() {
  return (
    <GenericErrorPage
      title={t`Page Not Found`}
      message={t`This page does not exist`}
    />
  );
}
