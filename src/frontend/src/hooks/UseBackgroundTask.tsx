import monitorBackgroundTask from '@lib/hooks/MonitorBackgroundTask';
import { useApi } from '../contexts/ApiContext';

/**
 * Hook for monitoring the progress of a background task running on the server
 */
export default function useBackgroundTask({
  title,
  message,
  taskId,
  onSuccess,
  onFailure,
  onComplete,
  onError
}: {
  title?: string;
  message: string;
  taskId?: string;
  onSuccess?: () => void;
  onFailure?: () => void;
  onComplete?: () => void;
  onError?: (error: Error) => void;
}) {
  const api = useApi();

  return monitorBackgroundTask({
    api: api,
    title: title,
    message: message,
    taskId: taskId,
    onSuccess: onSuccess,
    onFailure: onFailure,
    onComplete: onComplete,
    onError: onError
  });
}
