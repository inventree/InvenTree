import { t } from '@lingui/macro';
import { Badge, Group, Text } from '@mantine/core';
import {
  IconCircleCheck,
  IconCirclePlus,
  IconQuestionMark
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useMemo } from 'react';

import { api } from '../../App';
import { AttachmentLink } from '../../components/items/AttachmentLink';
import {
  PassFailButton,
  YesNoButton
} from '../../components/items/YesNoButton';
import { RenderUser } from '../../components/render/User';
import { renderDate } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { UserRoles } from '../../enums/Roles';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import {
  BooleanColumn,
  DateColumn,
  DescriptionColumn,
  NoteColumn
} from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowAction, RowDeleteAction, RowEditAction } from '../RowActions';

export default function StockItemTestResultTable({
  partId,
  itemId
}: {
  partId: number;
  itemId: number;
}) {
  const user = useUserState();
  const table = useTable('stocktests');

  // Query to fetch test templates associated with the part
  const testTemplates = useQuery({
    queryKey: ['testtemplates', partId],
    queryFn: async () => {
      if (!partId || !itemId) {
        return [];
      }

      return await api
        .get(apiUrl(ApiEndpoints.part_test_template_list), {
          params: {
            part: partId
          }
        })
        .then((response) => response.data)
        .catch(() => []);
    }
  });

  // Format the test results based on the returned data
  const formatRecords = useCallback(
    (records: any[]): any[] => {
      let resultMap: Record<string, any> = {};
      let resultList: any[] = [];

      // Iterate through the returned records
      // Note that the results are sorted by newest first,
      // to ensure that the most recent result is displayed "on top"
      records
        .sort((a, b) => {
          let aDate = new Date(a.date);
          let bDate = new Date(b.date);
          if (aDate < bDate) {
            return -1;
          } else if (aDate > bDate) {
            return 1;
          } else {
            return 0;
          }
        })
        .forEach((record, _idx) => {
          let key = record.key;

          // Most recent record is first
          if (!resultMap[key]) {
            resultMap[key] = {
              ...record,
              old: [],
              template: testTemplates?.data?.find((t: any) => t.key == key)
            };
          } else {
            resultMap[key]['old'].push(record);
          }
        });

      // Now, re-create the original list of records
      records.forEach((record, _idx) => {
        let key = record.key;

        // Check if the record is already in the list
        if (!resultList.find((r) => r.key == key)) {
          resultList.push(resultMap[key]);
        }
      });

      // Also, check if there are any templates which have not been accounted for
      testTemplates?.data?.forEach((template: any, index: number) => {
        // Check if the record is already in the list
        if (!resultList.find((r) => r.key == template.key)) {
          resultList.push({
            pk: `new-${index}`,
            template: template,
            old: []
          });
        }
      });

      return resultList;
    },
    [testTemplates.data]
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
              <Text italic={!record.template}>
                {record.template?.test_name ?? record.test}
              </Text>
              {(record.old?.length ?? 0) > 0 && (
                <Text italic>+{record.old.length}</Text>
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
        accessor: 'template.description'
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
