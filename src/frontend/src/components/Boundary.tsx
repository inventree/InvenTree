import { t } from '@lingui/macro';
import { Alert } from '@mantine/core';
import { ErrorBoundary, FallbackRender } from '@sentry/react';
import { IconExclamationCircle } from '@tabler/icons-react';
import { ReactNode, useCallback } from 'react';

function DefaultFallback(): ReactNode {
  return (
    <Alert
      color="red"
      icon={<IconExclamationCircle />}
      title={t`Error rendering component`}
    >
      {t`An error occurred while rendering this component. Refer to the console for more information.`}
    </Alert>
  );
}

export function Boundary({
  children,
  label,
  fallback
}: {
  children: ReactNode;
  label: string;
  fallback?: React.ReactElement | FallbackRender | undefined;
}): ReactNode {
  const onError = useCallback(
    (error: Error, componentStack: string, eventId: string) => {
      console.error(`Error rendering component: ${label}`);
      console.error(error, componentStack);
    },
    []
  );

  return (
    <ErrorBoundary fallback={fallback ?? <DefaultFallback />} onError={onError}>
      {children}
    </ErrorBoundary>
  );
}
