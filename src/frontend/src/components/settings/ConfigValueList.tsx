import { Code, Text } from '@mantine/core';

import { ApiEndpoints, apiUrl } from '@lib/index';
import { Trans } from '@lingui/react/macro';
import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';
import { api } from '../../App';

export function ConfigValueList({ keys }: Readonly<{ keys: string[] }>) {
  const { data, isLoading } = useQuery({
    queryKey: ['config'],
    queryFn: async () => {
      return api.get(apiUrl(ApiEndpoints.config_list)).then((res) => {
        return res.data;
      });
    }
  });

  const totalData = useMemo(() => {
    if (!data) return [];
    return keys.map((key) => {
      return {
        key: key,
        value: data.find((item: any) => item.key === key)
      };
    });
  }, [isLoading, data, keys]);

  return (
    <span>
      {totalData.map((vals) => (
        <Text key={vals.key}>
          <Trans>
            <Code>{vals.key}</Code> is set via {vals.value?.source} and was last
            set {vals.value.accessed}
          </Trans>
        </Text>
      ))}
    </span>
  );
}
