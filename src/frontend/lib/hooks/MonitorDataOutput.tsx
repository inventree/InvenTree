import { plural, t } from '@lingui/core/macro';
import { Anchor } from '@mantine/core';
import { useDocumentVisibility } from '@mantine/hooks';
import { notifications, showNotification } from '@mantine/notifications';
import {
  IconAlertTriangle,
  IconCircleCheck,
  IconExclamationCircle
} from '@tabler/icons-react';
import { type QueryClient, useQuery } from '@tanstack/react-query';
import type { AxiosInstance } from 'axios';
import { useEffect, useState } from 'react';
import { ProgressBar } from '../components/ProgressBar';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { apiUrl } from '../functions/Api';

const MAX_DISPLAYED_WARNINGS = 5;

export type MonitorDataOutputProps = {
  api: AxiosInstance;
  queryClient?: QueryClient;
  title: string;
  hostname?: string;
  id?: number;
};

/**
 * Hook for monitoring a data output process running on the server
 */
export default function useMonitorDataOutput(props: MonitorDataOutputProps) {
  const visibility = useDocumentVisibility();

  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (!!props.id) {
      setLoading(true);
      showNotification({
        id: `data-output-${props.id}`,
        title: props.title,
        loading: true,
        autoClose: false,
        withCloseButton: false,
        message: <ProgressBar size='lg' value={0} progressLabel />
      });
    } else setLoading(false);
  }, [props.id, props.title]);

  useQuery(
    {
      enabled: !!props.id && loading && visibility === 'visible',
      refetchInterval: 500,
      queryKey: ['data-output', props.id, props.title],
      queryFn: () =>
        props.api
          .get(apiUrl(ApiEndpoints.data_output, props.id))
          .then((response) => {
            const data = response?.data ?? {};
            const warnings: string[] = data.warnings ?? [];
            const remainingWarnings = warnings.length - MAX_DISPLAYED_WARNINGS;
            const warningList = warnings.length > 0 && (
              <>
                <ul
                  style={{
                    maxHeight: 200,
                    overflowY: 'auto',
                    overflowWrap: 'anywhere'
                  }}
                >
                  {warnings.slice(0, MAX_DISPLAYED_WARNINGS).map((warning) => (
                    <li key={warning} style={{ whiteSpace: 'pre-wrap' }}>
                      {warning}
                    </li>
                  ))}
                </ul>
                {remainingWarnings > 0 && (
                  <div>
                    {plural(remainingWarnings, {
                      one: '# more warning',
                      other: '# more warnings'
                    })}
                  </div>
                )}
              </>
            );

            if (!!data.errors || !!data.error) {
              setLoading(false);

              const error: string =
                data?.error ?? data?.errors?.error ?? t`Process failed`;

              notifications.update({
                id: `data-output-${props.id}`,
                loading: false,
                icon: <IconExclamationCircle />,
                autoClose: 2500,
                withCloseButton: true,
                title: props.title,
                message: error,
                color: 'red'
              });
            } else if (data.complete) {
              setLoading(false);
              const base = props.hostname ?? window.location.origin;
              const downloadUrl = data.output
                ? new URL(data.output, base).toString()
                : undefined;

              notifications.update({
                id: `data-output-${props.id}`,
                loading: false,
                autoClose: warnings.length > 0 ? false : 2500,
                withCloseButton: true,
                title: props.title,
                message: (
                  <>
                    {warnings.length > 0
                      ? t`Process completed with warnings`
                      : t`Process completed successfully`}
                    {warningList}
                    {downloadUrl && (
                      <>
                        <br />
                        <Anchor
                          href={downloadUrl}
                          target='_blank'
                          rel='noopener noreferrer'
                        >
                          {t`Open output`}
                        </Anchor>
                      </>
                    )}
                  </>
                ),
                color: warnings.length > 0 ? 'yellow' : 'green',
                icon:
                  warnings.length > 0 ? (
                    <IconAlertTriangle />
                  ) : (
                    <IconCircleCheck />
                  )
              });

              if (downloadUrl) {
                window.open(downloadUrl, '_blank');
              }
            } else {
              notifications.update({
                id: `data-output-${props.id}`,
                loading: true,
                autoClose: false,
                withCloseButton: false,
                message: (
                  <>
                    <ProgressBar
                      size='lg'
                      maximum={data.total}
                      value={data.progress}
                      progressLabel={data.total > 0}
                      animated
                    />
                    {warningList}
                  </>
                )
              });
            }

            return data;
          })
          .catch((error: Error) => {
            console.error('Error in useMonitorDataOutput:', error);
            setLoading(false);
            notifications.update({
              id: `data-output-${props.id}`,
              loading: false,
              autoClose: 2500,
              withCloseButton: true,
              title: props.title,
              message: error.message || t`Process failed`,
              color: 'red'
            });
            return {};
          })
    },
    props.queryClient
  );
}
