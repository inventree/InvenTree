import { t } from '@lingui/macro';
import { Badge, Group, Text, Tooltip } from '@mantine/core';
import { IconCircleCheck, IconCirclePlus } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo } from 'react';

import { api } from '../../App';
import { AttachmentLink } from '../../components/items/AttachmentLink';
import { PassFailButton } from '../../components/items/YesNoButton';
import { RenderUser } from '../../components/render/User';
import { renderDate } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { UserRoles } from '../../enums/Roles';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { DescriptionColumn, NoteColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowDeleteAction, RowEditAction } from '../RowActions';

export default function StockItemTestResultTable({
  partId,
  itemId
}: {
  partId: number;
  itemId: number;
}) {
  const user = useUserState();
  const table = useTable('stocktests');

  // Fetch the test templates required for this stock item
  const { data: testTemplates } = useQuery({
    queryKey: ['stocktesttemplates', partId],
    queryFn: async () => {
      if (!partId) {
        return [];
      }

      return api
        .get(apiUrl(ApiEndpoints.part_test_template_list), {
          params: {
            part: partId,
            include_inherited: true
          }
        })
        .then((response) => response.data)
        .catch((error) => []);
    }
  });

  useEffect(() => {
    table.refreshTable();
  }, [testTemplates]);

  // Format the test results based on the returned data
  const formatRecords = useCallback(
    (records: any[]): any[] => {
      let results = testTemplates.map((template: any) => {
        return {
          ...template,
          results: [],
          value: undefined,
          result: undefined,
          attachment: undefined,
          date: undefined,
          note: undefined
        };
      });

      // Iterate through the returned records
      // Note that the results are sorted by oldest first,
      // to ensure that the most recent result is displayed "on top"
      records
        .sort((a, b) => {
          let aDate = new Date(a.date);
          let bDate = new Date(b.date);
          if (aDate < bDate) {
            return 1;
          } else if (aDate > bDate) {
            return -1;
          } else {
            return 0;
          }
        })
        .forEach((record, _idx) => {
          // Find matching template
          let templateIndex = results.findIndex(
            (r: any) => r.pk == record.template
          );
          if (templateIndex >= 0) {
            results[templateIndex].results.push(record);
            results[templateIndex].value = record.value;
            results[templateIndex].result = record.result;
            results[templateIndex].attachment = record.attachment;
            results[templateIndex].date = record.date;
            results[templateIndex].note = record.note;
          }
        });

      return results;
    },
    [testTemplates]
  );

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'test',
        title: t`Test`,
        switchable: false,
        sortable: true,
        render: (record: any) => {
          return (
            <Group position="apart">
              <Text>{record.test_name}</Text>
              {record.results.length > 0 && (
                <Tooltip label={t`Test Results`}>
                  <Badge color="lightblue" variant="filled">
                    {record.results.length}
                  </Badge>
                </Tooltip>
              )}
            </Group>
          );
        }
      },
      {
        accessor: 'result',
        title: t`Result`,
        switchable: false,
        sortable: true,
        render: (record: any) => {
          if (record.result === undefined) {
            return (
              <Badge color="lightblue" variant="filled">{t`No Result`}</Badge>
            );
          } else {
            return <PassFailButton value={record.result} />;
          }
        }
      },
      DescriptionColumn({
        accessor: 'description'
      }),
      {
        accessor: 'value',
        title: t`Value`
      },
      {
        accessor: 'attachment',
        title: t`Attachment`,
        render: (record: any) =>
          record.attachment && <AttachmentLink attachment={record.attachment} />
      },
      NoteColumn(),
      {
        accessor: 'date',
        sortable: true,
        title: t`Date`,
        render: (record: any) => {
          return (
            <Group position="apart">
              {renderDate(record.date)}
              {record.user_detail && (
                <RenderUser instance={record.user_detail} />
              )}
            </Group>
          );
        }
      }
    ];
  }, []);

  const rowActions = useCallback(
    (record: any) => {
      return [
        {
          title: t`Pass Test`,
          color: 'green',
          icon: <IconCircleCheck />,
          hidden:
            record?.template?.requires_attachment ||
            record?.template?.requires_value ||
            record.result
        },
        {
          title: t`Add`,
          tooltip: t`Add Test Result`,
          color: 'green',
          icon: <IconCirclePlus />,
          hidden: !user.hasAddRole(UserRoles.stock)
        },
        RowEditAction({
          tooltip: t`Edit Test Result`,
          hidden: !user.hasChangeRole(UserRoles.stock)
        }),
        RowDeleteAction({
          tooltip: t`Delete Test Result`,
          hidden: !user.hasDeleteRole(UserRoles.stock)
        })
      ];
    },
    [user]
  );

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.stock_test_result_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        dataFormatter: formatRecords,
        enablePagination: false,
        rowActions: rowActions,
        params: {
          stock_item: itemId,
          user_detail: true,
          attachment_detail: true
        }
      }}
    />
  );
}
