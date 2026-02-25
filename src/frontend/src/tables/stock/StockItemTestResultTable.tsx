import { t } from '@lingui/core/macro';
import { Badge, Group, Text, Tooltip } from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import {
  IconCircleCheck,
  IconCirclePlus,
  IconInfoCircle
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { DataTable, type DataTableRowExpansionProps } from 'mantine-datatable';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { AddItemButton } from '@lib/components/AddItemButton';
import {
  type RowAction,
  RowActions,
  RowDeleteAction,
  RowEditAction
} from '@lib/components/RowActions';
import { PassFailButton } from '@lib/components/YesNoButton';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import type { TableColumn } from '@lib/types/Tables';
import { AttachmentLink } from '../../components/items/AttachmentLink';
import { useApi } from '../../contexts/ApiContext';
import { formatDate } from '../../defaults/formatters';
import { useTestResultFields } from '../../forms/StockForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useGlobalSettingsState } from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';
import {
  DateColumn,
  DescriptionColumn,
  NoteColumn,
  UserColumn
} from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import RowExpansionIcon from '../RowExpansionIcon';

export default function StockItemTestResultTable({
  partId,
  itemId
}: Readonly<{
  partId: number;
  itemId: number;
}>) {
  const api = useApi();
  const user = useUserState();
  const table = useTable('stocktests');

  const globalSettings = useGlobalSettingsState();
  const includeTestStation = useMemo(
    () => globalSettings.isSet('TEST_STATION_DATA'),
    [globalSettings]
  );
  // Fetch the test templates required for this stock item
  const { data: testTemplates } = useQuery({
    queryKey: ['stocktesttemplates', partId, itemId],
    queryFn: async () => {
      if (!partId) {
        return [];
      }

      return api
        .get(apiUrl(ApiEndpoints.part_test_template_list), {
          params: {
            part: partId,
            include_inherited: true,
            enabled: true
          }
        })
        .then((response) => response.data);
    }
  });

  useEffect(() => {
    table.refreshTable();
  }, [testTemplates]);

  // Format the test results based on the returned data
  const formatRecords = useCallback(
    (records: any[]): any[] => {
      // Construct a list of test templates
      const results =
        testTemplates?.map((template: any) => {
          return {
            ...template,
            templateId: template.pk,
            results: []
          };
        }) ?? [];

      // If any of the tests results point to templates which we do not have, add them in
      records.forEach((record) => {
        if (!results.find((r: any) => r.templateId == record.template)) {
          results.push({
            ...record.template_detail,
            templateId: record.template,
            results: []
          });
        }
      });

      // Iterate through the returned records
      // Note that the results are sorted by oldest first,
      // to ensure that the most recent result is displayed "on top"
      records
        .sort((a: any, b: any) => {
          return a.pk > b.pk ? 1 : -1;
        })
        .forEach((record) => {
          // Find matching template
          const idx = results.findIndex(
            (r: any) => r.templateId == record.template
          );
          if (idx >= 0) {
            results[idx] = {
              ...results[idx],
              ...record
            };

            results[idx].results.push(record);
          }
        });

      return results;
    },
    [partId, itemId, testTemplates]
  );

  const constructTableColumns = useCallback(
    (child: boolean) => {
      return [
        {
          accessor: 'test',
          title: t`Test`,
          switchable: false,
          sortable: true,
          render: (record: any) => {
            const enabled = record.enabled ?? record.template_detail?.enabled;
            const installed =
              record.stock_item != undefined && record.stock_item != itemId;

            const multipleResults = record.results && record.results.length > 1;

            return (
              <Group justify='space-between' wrap='nowrap'>
                <Group gap='xs'>
                  {!child && (
                    <RowExpansionIcon
                      enabled={multipleResults}
                      expanded={table.isRowExpanded(record.pk)}
                    />
                  )}
                  <Text
                    style={{ fontStyle: installed ? 'italic' : undefined }}
                    c={enabled ? undefined : 'red'}
                  >
                    {!record.templateId && '- '}
                    {record.test_name ?? record.template_detail?.test_name}
                  </Text>
                </Group>
                <Group justify='right'>
                  {record.results && record.results.length > 1 && (
                    <Tooltip label={t`Test Results`}>
                      <Badge color='lightblue' variant='filled'>
                        {record.results.length}
                      </Badge>
                    </Tooltip>
                  )}
                  {installed && (
                    <Tooltip label={t`Test result for installed stock item`}>
                      <IconInfoCircle size={16} color='blue' />
                    </Tooltip>
                  )}
                </Group>
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
                <Badge color='lightblue' variant='filled'>{t`No Result`}</Badge>
              );
            } else {
              return <PassFailButton value={record.result} />;
            }
          }
        },
        DescriptionColumn({}),
        {
          accessor: 'value',
          title: t`Value`
        },
        {
          accessor: 'attachment',
          title: t`Attachment`,
          render: (record: any) =>
            record.attachment && (
              <AttachmentLink attachment={record.attachment} />
            ),
          noContext: true
        },
        NoteColumn({}),
        DateColumn({}),
        UserColumn({
          accessor: 'user_detail',
          ordering: 'user'
        }),
        {
          accessor: 'test_station',
          sortable: true,
          title: t`Test station`,
          hidden: !includeTestStation
        },
        {
          accessor: 'started_datetime',
          sortable: true,
          title: t`Started`,
          hidden: !includeTestStation,
          render: (record: any) => {
            return (
              <Group justify='space-between'>
                {formatDate(record.started_datetime, {
                  showTime: true,
                  showSeconds: true
                })}
              </Group>
            );
          }
        },
        {
          accessor: 'finished_datetime',
          sortable: true,
          title: t`Finished`,
          hidden: !includeTestStation,
          render: (record: any) => {
            return (
              <Group justify='space-between'>
                {formatDate(record.finished_datetime, {
                  showTime: true,
                  showSeconds: true
                })}
              </Group>
            );
          }
        }
      ];
    },
    [itemId, includeTestStation, table.expandedRecords]
  );

  const tableColumns: TableColumn[] = useMemo(() => {
    return constructTableColumns(false);
  }, [itemId, includeTestStation, table.expandedRecords]);

  const [selectedTemplate, setSelectedTemplate] = useState<number | undefined>(
    undefined
  );

  const newResultFields: ApiFormFieldSet = useTestResultFields({
    partId: partId,
    itemId: itemId,
    templateId: selectedTemplate,
    editing: false
  });

  const editResultFields: ApiFormFieldSet = useTestResultFields({
    partId: partId,
    itemId: itemId,
    templateId: selectedTemplate,
    editing: true
  });

  const newTestModal = useCreateApiFormModal({
    url: ApiEndpoints.stock_test_result_list,
    fields: useMemo(() => ({ ...newResultFields }), [newResultFields]),
    initialData: {
      template: selectedTemplate,
      result: true
    },
    title: t`Add Test Result`,
    table: table,
    successMessage: t`Test result added`
  });

  const [selectedTest, setSelectedTest] = useState<number>(0);

  const editTestModal = useEditApiFormModal({
    url: ApiEndpoints.stock_test_result_list,
    pk: selectedTest,
    fields: useMemo(() => ({ ...editResultFields }), [editResultFields]),
    title: t`Edit Test Result`,
    onFormSuccess: () => table.refreshTable,
    successMessage: t`Test result updated`
  });

  const deleteTestModal = useDeleteApiFormModal({
    url: ApiEndpoints.stock_test_result_list,
    pk: selectedTest,
    title: t`Delete Test Result`,
    table: table,
    successMessage: t`Test result deleted`
  });

  const passTest = useCallback(
    (templateId: number) => {
      api
        .post(apiUrl(ApiEndpoints.stock_test_result_list), {
          template: templateId,
          stock_item: itemId,
          result: true
        })
        .then(() => {
          table.refreshTable();
          showNotification({
            title: t`Test Passed`,
            message: t`Test result has been recorded`,
            color: 'green'
          });
        })
        .catch(() => {
          showNotification({
            title: t`Error`,
            message: t`Failed to record test result`,
            color: 'red'
          });
        });
    },
    [itemId]
  );

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      if (record.stock_item != undefined && record.stock_item != itemId) {
        // Test results for other stock items cannot be edited
        return [];
      }

      return [
        {
          title: t`Pass Test`,
          color: 'green',
          icon: <IconCircleCheck />,
          hidden:
            !record.templateId ||
            !!record.choices ||
            record?.requires_attachment ||
            record?.requires_value ||
            record.result,
          onClick: () => passTest(record.templateId)
        },
        {
          title: t`Add`,
          tooltip: t`Add Test Result`,
          color: 'green',
          icon: <IconCirclePlus />,
          hidden: !user.hasAddRole(UserRoles.stock) || !record.templateId,
          onClick: () => {
            setSelectedTemplate(record.templateId);
            newTestModal.open();
          }
        },
        RowEditAction({
          tooltip: t`Edit Test Result`,
          hidden:
            !user.hasChangeRole(UserRoles.stock) || !record.template_detail,
          onClick: () => {
            setSelectedTest(record.pk);
            editTestModal.open();
          }
        }),
        RowDeleteAction({
          tooltip: t`Delete Test Result`,
          hidden:
            !user.hasDeleteRole(UserRoles.stock) || !record.template_detail,
          onClick: () => {
            setSelectedTest(record.pk);
            deleteTestModal.open();
          }
        })
      ];
    },
    [user, itemId]
  );

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'required',
        label: t`Required`,
        description: t`Show results for required tests`
      },
      {
        name: 'include_installed',
        label: t`Include Installed`,
        description: t`Show results for installed stock items`
      },
      {
        name: 'result',
        label: t`Passed`,
        description: t`Show only passed tests`
      },
      {
        name: 'enabled',
        label: t`Enabled`,
        description: t`Show results for enabled tests`
      }
    ];
  }, []);

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add-test-result'
        tooltip={t`Add Test Result`}
        onClick={() => {
          setSelectedTemplate(undefined);
          newTestModal.open();
        }}
        hidden={!user.hasAddRole(UserRoles.stock)}
      />
    ];
  }, [user]);

  // Row expansion controller
  const rowExpansion: DataTableRowExpansionProps<any> = useMemo(() => {
    const cols: any = [
      ...constructTableColumns(true),
      {
        accessor: 'actions',
        title: '  ',
        hidden: false,
        switchable: false,
        width: 50,
        render: (record: any) => (
          <RowActions actions={rowActions(record) ?? []} />
        )
      }
    ];

    return {
      allowMultiple: true,
      expandable: ({ record }: { record: any }) => {
        return (
          table.isRowExpanded(record.pk) ||
          (record.results && record.results.length > 1)
        );
      },
      content: ({ record }: { record: any }) => {
        if (!record || !record.results || record.results.length < 2) {
          return null;
        }

        const results = record?.results ?? [];

        return (
          <DataTable
            key={record.pk}
            idAccessor={'test'}
            noHeader
            columns={cols}
            records={results.slice(0, -1)}
          />
        );
      }
    };
  }, [constructTableColumns, table.isRowExpanded]);

  return (
    <>
      {newTestModal.modal}
      {editTestModal.modal}
      {deleteTestModal.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.stock_test_result_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          dataFormatter: formatRecords,
          enablePagination: false,
          tableActions: tableActions,
          tableFilters: tableFilters,
          rowActions: rowActions,
          rowExpansion: rowExpansion,
          params: {
            stock_item: itemId,
            user_detail: true,
            attachment_detail: true,
            template_detail: true
          }
        }}
      />
    </>
  );
}
