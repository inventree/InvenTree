import { Table } from '@mantine/core';

import { ApiEndpoints, apiUrl } from '@lib/index';
import { Trans } from '@lingui/react/macro';
import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';
import { api } from '../../App';
import { formatDate } from '../../defaults/formatters';

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
      <Table withColumnBorders withTableBorder striped>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>
              <Trans>Setting</Trans>
            </Table.Th>
            <Table.Th>
              <Trans>Source</Trans>
            </Table.Th>
            <Table.Th>
              <Trans>Updated</Trans>
            </Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {totalData.map((vals) => (
            <Table.Tr key={vals.key}>
              <Table.Td>{vals.key}</Table.Td>
              <Table.Td>{vals.value?.source}</Table.Td>
              <Table.Td>
                {formatDate(vals.value?.accessed, { showTime: true })}
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </span>
  );
}
