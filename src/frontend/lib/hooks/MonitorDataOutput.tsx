import { t } from '@lingui/core/macro';
import { useDocumentVisibility } from '@mantine/hooks';
import { notifications, showNotification } from '@mantine/notifications';
import { IconCircleCheck, IconExclamationCircle } from '@tabler/icons-react';
import { type QueryClient, useQuery } from '@tanstack/react-query';
import type { AxiosInstance } from 'axios';
import { useEffect, useState } from 'react';
import { ProgressBar } from '../components/ProgressBar';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { apiUrl } from '../functions/Api';

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

            if (!!data.errors || !!data.error) {
              setLoading(false);

              const error: string =
                data?.error ?? data?.errors?.error ?? t`Process failed`;

              notifications.update({
                id: `data-output-${props.id}`,
                loading: false,
                icon: <IconExclamationCircle />,
                autoClose: 2500,
                title: props.title,
                message: error,
                color: 'red'
              });
            } else if (data.complete) {
              setLoading(false);
              notifications.update({
                id: `data-output-${props.id}`,
                loading: false,
                autoClose: 2500,
                title: props.title,
                message: t`Process completed successfully`,
                color: 'green',
                icon: <IconCircleCheck />
              });

              if (data.output) {
                const url = data.output;
                const base = props.hostname ?? window.location.origin;

                const downloadUrl = new URL(url, base);

                window.open(downloadUrl.toString(), '_blank');
              }
            } else {
              notifications.update({
                id: `data-output-${props.id}`,
                loading: true,
                autoClose: false,
                withCloseButton: false,
                message: (
                  <ProgressBar
                    size='lg'
                    maximum={data.total}
                    value={data.progress}
                    progressLabel={data.total > 0}
                    animated
                  />
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
