import { t } from '@lingui/core/macro';
import { Alert, Group, Stack, Text } from '@mantine/core';
import { ErrorBoundary, type FallbackRender } from '@sentry/react';
import { IconExclamationCircle, IconInfoCircle } from '@tabler/icons-react';
import { type ReactNode, useCallback, useState } from 'react';
import { CopyButton } from './CopyButton';

/**
 * Construct a plain-text error report, suitable for copying into a bug report
 */
export function formatErrorReport({
  label,
  error,
  componentStack
}: {
  label: string;
  error: unknown;
  componentStack?: string;
}): string {
  const lines: string[] = [
    `Error rendering component: ${label}`,
    `Timestamp: ${new Date().toISOString()}`,
    `URL: ${window.location.href}`,
    `User Agent: ${navigator.userAgent}`,
    ''
  ];

  if (error instanceof Error) {
    lines.push(`${error.name}: ${error.message}`);
    if (error.stack) {
      lines.push('', 'Stack trace:', error.stack);
    }
  } else {
    lines.push(String(error));
  }

  if (componentStack) {
    lines.push('', 'Component stack:', componentStack.trim());
  }

  return lines.join('\n');
}

export function DefaultFallback({
  title,
  error,
  details
}: Readonly<{
  title: string;
  error: string | null;
  details?: string | null;
}>): ReactNode {
  const copyValue = details ?? error;

  return (
    <>
      <Alert
        color='red'
        icon={<IconExclamationCircle />}
        title={`INVE-E17: ${t`Error rendering component`}: ${title}`}
      >
        <Stack gap='xs'>
          <Text size='sm'>
            {t`An error occurred while rendering this component.`}
          </Text>
          <Text size='sm'>
            {t`Try reloading the page, or contact your administrator if the problem persists.`}
          </Text>
        </Stack>
      </Alert>
      {error && (
        <Alert color='red' icon={<IconInfoCircle />} title={t`Error Details`}>
          <Stack gap='xs'>
            <Text size='sm'>{error}</Text>
            {copyValue && (
              <Group justify='flex-start'>
                <CopyButton
                  value={copyValue}
                  label={t`Copy error information`}
                  tooltip={t`Copy full error information to the clipboard`}
                  color='red'
                  variant='light'
                />
              </Group>
            )}
          </Stack>
        </Alert>
      )}
    </>
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
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [errorDetails, setErrorDetails] = useState<string | null>(null);

  const onError = useCallback(
    (error: unknown, componentStack: string | undefined, eventId: string) => {
      console.error(`ERR: Error rendering component: ${label}`);
      console.error(error);
      setErrorMessage(error instanceof Error ? error.message : String(error));
      setErrorDetails(formatErrorReport({ label, error, componentStack }));
    },
    [label]
  );

  return (
    <ErrorBoundary
      fallback={
        fallback ?? (
          <DefaultFallback
            title={label}
            error={errorMessage}
            details={errorDetails}
          />
        )
      }
      onError={onError}
    >
      {children}
    </ErrorBoundary>
  );
}
