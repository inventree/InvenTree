import { t } from '@lingui/macro';
import { Alert } from '@mantine/core';
import { ErrorBoundary, FallbackRender } from '@sentry/react';
import { IconExclamationCircle } from '@tabler/icons-react';
import { ReactNode, useCallback } from 'react';

function DefaultFallback({ title }: { title: String }): ReactNode {
  return (
    <Alert
      color="red"
      icon={<IconExclamationCircle />}
      title={t`Error rendering component` + `: ${title}`}
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
    (error: unknown, componentStack: string | undefined, eventId: string) => {
      console.error(`Error rendering component: ${label}`);
      console.error(error, componentStack);
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
