import { t } from '@lingui/macro';

import GenericErrorPage from './GenericErrorPage';

export default function ServerError({ status }: Readonly<{ status?: number }>) {
  return (
    <GenericErrorPage
      title={t`Server Error`}
      message={t`A server error occurred`}
      status={status}
    />
  );
}
