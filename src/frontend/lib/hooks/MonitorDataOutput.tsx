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

/**
 * Hook for monitoring a data output process running on the server
 */
export default function monitorDataOutput({
  api,
  queryClient,
  title,
  hostname,
  id
}: {
  api: AxiosInstance;
  queryClient?: QueryClient;
  title: string;
  hostname?: string;
  id?: number;
}) {
  const visibility = useDocumentVisibility();

  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (!!id) {
      setLoading(true);
      showNotification({
        id: `data-output-${id}`,
        title: title,
        loading: true,
        autoClose: false,
        withCloseButton: false,
        message: <ProgressBar size='lg' value={0} progressLabel />
      });
    } else setLoading(false);
  }, [id, title]);

  useQuery(
    {
      enabled: !!id && loading && visibility === 'visible',
      refetchInterval: 500,
      queryKey: ['data-output', id, title],
      queryFn: () =>
        api
          .get(apiUrl(ApiEndpoints.data_output, id))
          .then((response) => {
            const data = response?.data ?? {};

            if (!!data.errors || !!data.error) {
              setLoading(false);

              const error: string =
                data?.error ?? data?.errors?.error ?? t`Process failed`;

              notifications.update({
                id: `data-output-${id}`,
                loading: false,
                icon: <IconExclamationCircle />,
                autoClose: 2500,
                title: title,
                message: error,
                color: 'red'
              });
            } else if (data.complete) {
              setLoading(false);
              notifications.update({
                id: `data-output-${id}`,
                loading: false,
                autoClose: 2500,
                title: title,
                message: t`Process completed successfully`,
                color: 'green',
                icon: <IconCircleCheck />
              });

              if (data.output) {
                const url = data.output;
                const base = hostname ?? window.location.origin;

                const downloadUrl = new URL(url, base);

                window.open(downloadUrl.toString(), '_blank');
              }
            } else {
              notifications.update({
                id: `data-output-${id}`,
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
            console.error('Error in monitorDataOutput:', error);
            setLoading(false);
            notifications.update({
              id: `data-output-${id}`,
              loading: false,
              autoClose: 2500,
              title: title,
              message: error.message || t`Process failed`,
              color: 'red'
            });
            return {};
          })
    },
    queryClient
  );
}
