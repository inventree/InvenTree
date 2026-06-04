import { t } from '@lingui/core/macro';
import { Alert, Stack, Text } from '@mantine/core';
import { ErrorBoundary, type FallbackRender } from '@sentry/react';
import { IconExclamationCircle } from '@tabler/icons-react';
import { type ReactNode, useCallback } from 'react';

export function DefaultFallback({
  title
}: Readonly<{ title: string }>): ReactNode {
  return (
    <Alert
      color='red'
      icon={<IconExclamationCircle />}
      title={`INVE-E17: ${t`Error rendering component`}: ${title}`}
    >
      <Stack gap='xs'>
        <Text size='sm'>
          {t`An error occurred while rendering this component. Refer to the console for more information.`}
        </Text>
        <Text size='sm'>
          {t`Try reloading the page, or contact your administrator if the problem persists.`}
        </Text>
      </Stack>
    </Alert>
  );
}

export function Boundary({
  children,
  label,
  fallback
}: Readonly<{
  children: ReactNode;
  label: string;
  fallback?: React.ReactElement<any> | FallbackRender;
}>): ReactNode {
  const onError = useCallback(
    (error: unknown, _componentStack: string | undefined, _eventId: string) => {
      console.error(`ERR: Error rendering component: ${label}`);
      console.error(error);
    },
    []
  );

  return (
    <ErrorBoundary
      fallback={fallback ?? <DefaultFallback title={label} />}
      onError={onError}
    >
      {children}
    </ErrorBoundary>
  );
}
