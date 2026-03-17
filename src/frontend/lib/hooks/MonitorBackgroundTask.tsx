import { useDocumentVisibility } from '@mantine/hooks';
import { notifications, showNotification } from '@mantine/notifications';
import {
  IconCircleCheck,
  IconCircleX,
  IconExclamationCircle
} from '@tabler/icons-react';
import { type QueryClient, useQuery } from '@tanstack/react-query';
import type { AxiosInstance } from 'axios';
import { useEffect, useState } from 'react';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { apiUrl } from '../functions/Api';

export type MonitorBackgroundTaskProps = {
  api: AxiosInstance;
  queryClient?: QueryClient;
  title?: string;
  message: string;
  errorMessage?: string;
  successMessage?: string;
  failureMessage?: string;
  taskId?: string;
  onSuccess?: () => void;
  onFailure?: () => void;
  onComplete?: () => void;
  onError?: (error: Error) => void;
};

/**
 * Hook for monitoring a background task running on the server
 */
export default function useMonitorBackgroundTask(
  props: MonitorBackgroundTaskProps
) {
  const visibility = useDocumentVisibility();

  const [tracking, setTracking] = useState<boolean>(false);

  useEffect(() => {
    if (!!props.taskId) {
      setTracking(true);
      showNotification({
        id: `background-task-${props.taskId}`,
        title: props.title,
        message: props.message,
        loading: true,
        autoClose: false,
        withCloseButton: false
      });
    } else {
      setTracking(false);
    }
  }, [props.taskId]);

  useQuery(
    {
      enabled: !!props.taskId && tracking && visibility === 'visible',
      refetchInterval: 500,
      queryKey: ['background-task', props.taskId],
      queryFn: () =>
        props.api
          .get(apiUrl(ApiEndpoints.task_overview, props.taskId))
          .then((response) => {
            const data = response?.data ?? {};

            if (data.complete) {
              setTracking(false);
              props.onComplete?.();

              notifications.update({
                id: `background-task-${props.taskId}`,
                title: props.title,
                loading: false,
                color: data.success ? 'green' : 'red',
                message: response.data?.success
                  ? (props.successMessage ?? props.message)
                  : (props.failureMessage ?? props.message),
                icon: response.data?.success ? (
                  <IconCircleCheck />
                ) : (
                  <IconCircleX />
                ),
                autoClose: 1000,
                withCloseButton: true
              });

              if (data.success) {
                props.onSuccess?.();
              } else {
                props.onFailure?.();
              }
            }

            return response;
          })
          .catch((error) => {
            console.error(
              `Error fetching background task status for task ${props.taskId}:`,
              error
            );
            setTracking(false);
            props.onError?.(error);

            notifications.update({
              id: `background-task-${props.taskId}`,
              title: props.title,
              loading: false,
              color: 'red',
              message: props.errorMessage ?? props.message,
              icon: <IconExclamationCircle color='red' />,
              autoClose: 5000,
              withCloseButton: true
            });
          })
    },
    props.queryClient
  );
}
