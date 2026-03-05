import monitorDataOutput from '@lib/hooks/MonitorDataOutput';
import { useApi } from '../contexts/ApiContext';
import { useLocalState } from '../states/LocalState';

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
  const { getHost } = useLocalState.getState();

  return monitorDataOutput({
    api: api,
    title: title,
    id: id,
    hostname: getHost()
  });
}
