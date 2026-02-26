import { ProgressBar } from '@lib/components/ProgressBar';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { t } from '@lingui/core/macro';
import { useDocumentVisibility } from '@mantine/hooks';
import { notifications, showNotification } from '@mantine/notifications';
import { IconCircleCheck, IconExclamationCircle } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { useApi } from '../contexts/ApiContext';
import { generateUrl } from '../functions/urls';

/**
 * Hook for monitoring a data output process running on the server
 */
export default function useDataOutput({
  title,
  id
}: {
  title: string;
  id?: number;
}) {
  const api = useApi();

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

  useQuery({
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
              const url = generateUrl(data.output);
              window.open(url.toString(), '_blank');
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
        .catch(() => {
          setLoading(false);
          notifications.update({
            id: `data-output-${id}`,
            loading: false,
            autoClose: 2500,
            title: title,
            message: t`Process failed`,
            color: 'red'
          });
          return {};
        })
  });
}
