import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import type { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import { useQuery } from '@tanstack/react-query';
import { useApi } from '../contexts/ApiContext';

export interface InstanceInfo {
  attachment_count: number;
  note_count: number;
  parameter_count: number;
}

const emptyInstanceInfo: InstanceInfo = {
  attachment_count: 0,
  note_count: 0,
  parameter_count: 0
};

/**
 * Fetch aggregated attachment/note/parameter counts for a single model instance.
 *
 * A single generic lookup which detail pages can use to drive their Attachments,
 * Notes and Parameters tab notification dots from one request, instead of each
 * tab independently querying its own list endpoint just to read a count.
 */
export function useInstanceInfo({
  modelType,
  modelId
}: {
  modelType?: ModelType;
  modelId?: number;
}) {
  const api = useApi();

  const query = useQuery<InstanceInfo>({
    queryKey: ['instance-info', modelType, modelId],
    enabled: !!modelType && !!modelId,
    queryFn: async () => {
      return api
        .get(apiUrl(ApiEndpoints.instance_info), {
          params: { model_type: modelType, model_id: modelId }
        })
        .then((response) => response.data ?? emptyInstanceInfo);
    }
  });

  return {
    instanceInfo: query.data ?? emptyInstanceInfo,
    instanceInfoQuery: query
  };
}
