import { t } from '@lingui/macro';
import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { getDetailUrl } from '../../functions/urls';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { DescriptionColumn, PartColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import { TableHoverCard } from '../TableHoverCard';

export default function ParametricPartTable({
  categoryId
}: {
  categoryId?: any;
}) {
  const table = useTable('parametric-parts');
  const user = useUserState();
  const navigate = useNavigate();

  const categoryParmeters = useQuery({
    queryKey: ['category-parameters', categoryId],
    queryFn: async () => {
      return api
        .get(apiUrl(ApiEndpoints.part_parameter_template_list), {
          params: {
            category: categoryId
          }
        })
        .then((response) => response.data)
        .catch((_error) => []);
    },
    refetchOnMount: true
  });

  const parameterColumns: TableColumn[] = useMemo(() => {
    let data = categoryParmeters.data ?? [];

    return data.map((template: any) => {
      return {
        accessor: `parameter_${template.pk}`,
        title: template.name,
        sortable: true,
        render: (record: any) => {
          // Find matching template parameter
          let parameter = record.parameters?.find(
            (p: any) => p.template == template.pk
          );

          if (!parameter) {
            return '-';
          }

          let extra: any[] = [];

          if (
            template.units &&
            parameter.data_numeric &&
            parameter.data_numeric != parameter.data
          ) {
            extra.push(`${parameter.data_numeric} [${template.units}]`);
          }

          return (
            <TableHoverCard
              value={parameter.data}
              extra={extra}
              title={t`Internal Units`}
            />
          );
        }
      };
    });
  }, [categoryParmeters.data]);

  const tableColumns: TableColumn[] = useMemo(() => {
    const partColumns: TableColumn[] = [
      {
        accessor: 'name',
        sortable: true,
        switchable: false,
        noWrap: true,
        render: (record: any) => PartColumn(record)
      },
      DescriptionColumn({}),
      {
        accessor: 'IPN',
        sortable: true
      }
    ];

    return [...partColumns, ...parameterColumns];
  }, [parameterColumns]);

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.part_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        enableDownload: false,
        params: {
          category: categoryId,
          cascade: true,
          category_detail: true,
          parameters: true
        },
        onRowClick: (record) => {
          if (record.pk) {
            navigate(getDetailUrl(ModelType.part, record.pk));
          }
        }
      }}
    />
  );
}
