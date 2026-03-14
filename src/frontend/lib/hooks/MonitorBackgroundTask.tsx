import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { useDocumentVisibility } from '@mantine/hooks';
import { showNotification } from '@mantine/notifications';
import {
  IconCircleCheck,
  IconCircleX,
  IconExclamationCircle
} from '@tabler/icons-react';
import { type QueryClient, useQuery } from '@tanstack/react-query';
import type { AxiosInstance } from 'axios';
import { useEffect, useState } from 'react';

/**
 * Hook for monitoring a background task running on the server
 */
export default function monitorBackgroundTask({
  api,
  queryClient,
  title,
  message,
  taskId,
  onSuccess,
  onFailure,
  onComplete,
  onError
}: {
  api: AxiosInstance;
  queryClient?: QueryClient;
  title?: string;
  message: string;
  taskId?: string;
  onSuccess?: () => void;
  onFailure?: () => void;
  onComplete?: () => void;
  onError?: (error: Error) => void;
}) {
  const visibility = useDocumentVisibility();

  const [tracking, setTracking] = useState<boolean>(false);

  useEffect(() => {
    if (!!taskId) {
      setTracking(true);
      showNotification({
        id: `background-task-${taskId}`,
        title: title,
        message: message,
        loading: true,
        autoClose: false,
        withCloseButton: false
      });
    } else {
      setTracking(false);
    }
  }, [taskId, title]);

  useQuery(
    {
      enabled: !!taskId && tracking && visibility === 'visible',
      refetchInterval: 250,
      queryKey: ['background-task', taskId],
      queryFn: () =>
        api
          .get(apiUrl(ApiEndpoints.task_overview, taskId))
          .then((response) => {
            const data = response?.data ?? {};

            if (data.complete) {
              setTracking(false);
              onComplete?.();

              showNotification({
                id: `background-task-${taskId}`,
                title: title,
                message: message,
                icon: response.data?.success ? (
                  <IconCircleCheck color='green' />
                ) : (
                  <IconCircleX color='red' />
                ),
                autoClose: 1000,
                withCloseButton: true
              });

              if (data.success) {
                onSuccess?.();
              } else {
                onFailure?.();
              }
            }
          })
          .catch((error) => {
            console.error(
              `Error fetching background task status for task ${taskId}:`,
              error
            );
            setTracking(false);
            onError?.(error);

            showNotification({
              id: `background-task-${taskId}`,
              title: title,
              message: message,
              icon: <IconExclamationCircle color='red' />,
              autoClose: 5000,
              withCloseButton: true
            });
          })
    },
    queryClient
  );
}
