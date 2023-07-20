import { Trans, t } from '@lingui/macro';
import { Container, Text, Title } from '@mantine/core';
import { useDocumentTitle } from '@mantine/hooks';
import { useEffect, useState } from 'react';
import { useRouteError } from 'react-router-dom';

import { LanguageContext } from '../contexts/LanguageContext';
import { ErrorResponse } from '../states/states';

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
    <LanguageContext>
      <Container>
        <Title>
          <Trans>Error</Trans>
        </Title>
        <Text>
          <Trans>Sorry, an unexpected error has occurred.</Trans>
        </Text>
        <Text>
          <i>{error.statusText || error.message}</i>
        </Text>
      </Container>
    </LanguageContext>
  );
}
