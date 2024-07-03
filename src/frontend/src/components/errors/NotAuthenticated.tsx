import { t } from '@lingui/macro';

import GenericErrorPage from './GenericErrorPage';

export default function NotAuthenticated() {
  return (
    <GenericErrorPage
      title={t`Not Authenticated`}
      message={t`You are not logged in.`}
    />
  );
}
