import { t } from '@lingui/macro';
import { Alert } from '@mantine/core';
import { ErrorBoundary, type FallbackRender } from '@sentry/react';
import { IconExclamationCircle } from '@tabler/icons-react';
import { type ReactNode, useCallback } from 'react';

function DefaultFallback({ title }: Readonly<{ title: string }>): ReactNode {
  return (
    <Alert
      color='red'
      icon={<IconExclamationCircle />}
      title={`${t`Error rendering component`}: ${title}`}
    >
      {t`An error occurred while rendering this component. Refer to the console for more information.`}
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
  fallback?: React.ReactElement | FallbackRender;
}>): ReactNode {
  const onError = useCallback(
    (error: unknown, componentStack: string | undefined, eventId: string) => {
      console.error(`ERR: Error rendering component: ${label}`);
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
