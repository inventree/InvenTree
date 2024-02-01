import { t } from '@lingui/macro';
import { Group, Text } from '@mantine/core';
import { ReactNode, useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { ApiFormFieldSet } from '../../components/forms/fields/ApiFormField';
import { Thumbnail } from '../../components/images/Thumbnail';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { UserRoles } from '../../enums/Roles';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowDeleteAction } from '../RowActions';

/**
 * Construct a table listing related parts for a given part
 */
export function RelatedPartTable({ partId }: { partId: number }): ReactNode {
  const table = useTable('relatedparts');

  const navigate = useNavigate();

  const user = useUserState();

  // Construct table columns for this table
  const tableColumns: TableColumn[] = useMemo(() => {
    function getPart(record: any) {
      if (record.part_1 == partId) {
        return record.part_2_detail;
      } else {
        return record.part_1_detail;
      }
    }

    return [
      {
        accessor: 'part',
        title: t`Part`,
        render: (record: any) => {
          let part = getPart(record);
          return (
            <Group
              noWrap={true}
              position="left"
              onClick={() => {
                navigate(`/part/${part.pk}/`);
              }}
            >
              <Thumbnail src={part.thumbnail || part.image} />
              <Text>{part.name}</Text>
            </Group>
          );
        }
      },
      {
        accessor: 'description',
        title: t`Description`,
        ellipsis: true,
        render: (record: any) => {
          return getPart(record).description;
        }
      }
    ];
  }, [partId]);

  const relatedPartFields: ApiFormFieldSet = useMemo(() => {
    return {
      part_1: {
        hidden: true
      },
      part_2: {}
    };
  }, []);

  const newRelatedPart = useCreateApiFormModal({
    url: ApiEndpoints.related_part_list,
    title: t`Add Related Part`,
    fields: relatedPartFields,
    initialData: {
      part_1: partId
    },
    onFormSuccess: table.refreshTable
  });

  const [selectedRelatedPart, setSelectedRelatedPart] = useState<
    number | undefined
  >(undefined);

  const deleteRelatedPart = useDeleteApiFormModal({
    url: ApiEndpoints.related_part_list,
    pk: selectedRelatedPart,
    title: t`Delete Related Part`,
    onFormSuccess: table.refreshTable
  });

  const tableActions: ReactNode[] = useMemo(() => {
    return [
      <AddItemButton
        tooltip={t`Add related part`}
        hidden={!user.hasAddRole(UserRoles.part)}
        onClick={() => newRelatedPart.open()}
      />
    ];
  }, [user]);

  const rowActions = useCallback(
    (record: any) => {
      return [
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.part),
          onClick: () => {
            setSelectedRelatedPart(record.pk);
            deleteRelatedPart.open();
          }
        })
      ];
    },
    [user]
  );

  return (
    <>
      {newRelatedPart.modal}
      {deleteRelatedPart.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.related_part_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            part: partId,
            category_detail: true
          },
          rowActions: rowActions,
          tableActions: tableActions
        }}
      />
    </>
  );
}
