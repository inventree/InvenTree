import { t } from '@lingui/core/macro';
import { Alert, Stack } from '@mantine/core';
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
        {t`An error occurred while rendering this component. Refer to the console for more information.`}
        {t`Try reloading the page, or contact your administrator if the problem persists.`}
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
    (error: unknown, componentStack: string | undefined, eventId: string) => {
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
