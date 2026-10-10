import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import type { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import { t } from '@lingui/core/macro';
import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';
import { useApi } from '../../contexts/ApiContext';
import type { DetailsField, DetailsTableProps } from './Details';

export function useParameterDetailsGrid({
  model_type,
  model_id
}: Readonly<{
  model_type: ModelType;
  model_id: number | string | undefined;
}>): DetailsTableProps {
  const api = useApi();

  const { data: parameters = [] } = useQuery({
    queryKey: ['parameter-details', model_type, model_id],
    enabled: !!model_id && !!model_type,
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.parameter_list), {
          params: { model_type, model_id, limit: 100 }
        })
        .then((res) => res.data?.results ?? [])
  });

  const { fields, item } = useMemo(() => {
    const item: Record<string, string> = {};
    const fields: DetailsField[] = parameters.map((param: any) => {
      const key = `param_${param.pk}`;
      const value =
        param.data +
        (param.template_detail?.units ? ` ${param.template_detail.units}` : '');
      item[key] = value;
      return {
        type: 'string' as const,
        name: key,
        label: param.template_detail?.name ?? String(param.pk),
        copy: true
      };
    });
    return { fields, item };
  }, [parameters]);

  return {
    title: t`Parameters`,
    fields: fields,
    item: item,
    showIcons: false
  };
}
