import useMonitorBackgroundTask, {
  type MonitorBackgroundTaskProps
} from '@lib/hooks/MonitorBackgroundTask';
import { useApi } from '../contexts/ApiContext';

/**
 * Hook for monitoring the progress of a background task running on the server
 */
export default function useBackgroundTask(
  props: Omit<MonitorBackgroundTaskProps, 'api'>
) {
  const api = useApi();

  return useMonitorBackgroundTask({
    ...props,
    api: api
  });
}
