import { t } from '@lingui/macro';
import { Badge, Group, Text, Tooltip } from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import { IconCircleCheck, IconCirclePlus } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { DataTable } from 'mantine-datatable';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { api } from '../../App';
import { AddItemButton } from '../../components/buttons/AddItemButton';
import { ApiFormFieldSet } from '../../components/forms/fields/ApiFormField';
import { AttachmentLink } from '../../components/items/AttachmentLink';
import { PassFailButton } from '../../components/items/YesNoButton';
import { RenderUser } from '../../components/render/User';
import { renderDate } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { UserRoles } from '../../enums/Roles';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { DescriptionColumn, NoteColumn } from '../ColumnRenderers';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowActions, RowDeleteAction, RowEditAction } from '../RowActions';

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
    queryKey: ['stocktesttemplates', partId, itemId],
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
        .catch((_error) => []);
    }
  });

  useEffect(() => {
    table.refreshTable();
  }, [testTemplates]);

  // Format the test results based on the returned data
  const formatRecords = useCallback(
    (records: any[]): any[] => {
      // Construct a list of test templates
      let results = testTemplates.map((template: any) => {
        return {
          ...template,
          templateId: template.pk,
          results: []
        };
      });

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
          let idx = results.findIndex(
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
              <Text italic={!record.templateId}>
                {!record.templateId && '- '}
                {record.test_name ?? record.template_detail?.test_name}
              </Text>
              {record.results && record.results.length > 1 && (
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

  const resultFields: ApiFormFieldSet = useMemo(() => {
    return {
      template: {
        filters: {
          include_inherited: true,
          part: partId
        }
      },
      result: {},
      value: {},
      attachment: {},
      notes: {},
      stock_item: {
        value: itemId,
        hidden: true
      }
    };
  }, [partId, itemId]);

  const [selectedTemplate, setSelectedTemplate] = useState<number | undefined>(
    undefined
  );

  const newTestModal = useCreateApiFormModal({
    url: ApiEndpoints.stock_test_result_list,
    fields: resultFields,
    initialData: {
      template: selectedTemplate,
      result: true
    },
    title: t`Add Test Result`,
    onFormSuccess: () => table.refreshTable(),
    successMessage: t`Test result added`
  });

  const [selectedTest, setSelectedTest] = useState<number | undefined>(
    undefined
  );

  const editTestModal = useEditApiFormModal({
    url: ApiEndpoints.stock_test_result_list,
    pk: selectedTest,
    fields: resultFields,
    title: t`Edit Test Result`,
    onFormSuccess: () => table.refreshTable(),
    successMessage: t`Test result updated`
  });

  const deleteTestModal = useDeleteApiFormModal({
    url: ApiEndpoints.stock_test_result_list,
    pk: selectedTest,
    title: t`Delete Test Result`,
    onFormSuccess: () => table.refreshTable(),
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
        });
    },
    [itemId]
  );

  const rowActions = useCallback(
    (record: any) => {
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
      }
    ];
  }, []);

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
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
  const rowExpansion: any = useMemo(() => {
    const cols: any = [
      ...tableColumns,
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
      content: ({ record }: { record: any }) => {
        if (!record || !record.results || record.results.length < 2) {
          return null;
        }

        const results = record?.results ?? [];

        return (
          <DataTable
            key={record.pk}
            noHeader
            columns={cols}
            records={results.slice(0, -1)}
          />
        );
      }
    };
  }, []);

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
