import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { Loader } from '@mantine/core';
import { useDocumentVisibility } from '@mantine/hooks';
import { hideNotification, showNotification } from '@mantine/notifications';
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
  taskId,
  onSuccess,
  onFailure,
  onComplete,
  onError
}: {
  api: AxiosInstance;
  queryClient?: QueryClient;
  title: string;
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
        loading: true,
        autoClose: false,
        withCloseButton: false,
        message: <Loader size='md' />
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
              hideNotification(`background-task-${taskId}`);

              onComplete?.();

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
            hideNotification(`background-task-${taskId}`);
            onError?.(error);
          })
    },
    queryClient
  );
}
