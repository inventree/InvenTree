import { t } from '@lingui/macro';
import { useDocumentTitle } from '@mantine/hooks';
import { useEffect, useState } from 'react';
import { useRouteError } from 'react-router-dom';

import { ErrorResponse } from '../states/states';
import GenericErrorPage from './errors/GenericErrorPage';

export default function ErrorPage() {
  const error = useRouteError() as ErrorResponse;
  const [title, setTitle] = useState(t`Error`);
  useDocumentTitle(title);

  useEffect(() => {
    if (error?.statusText) {
      setTitle(t`Error: ${error.statusText}`);
    }
  }, [error]);

  return (
    <GenericErrorPage
      title={title}
      message={t`An unexpected error has occurred`}
    />
  );
}
