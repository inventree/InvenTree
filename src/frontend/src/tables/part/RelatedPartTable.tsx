import { t } from '@lingui/macro';
import { Group, Text } from '@mantine/core';
import { type ReactNode, useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import type { ApiFormFieldSet } from '../../components/forms/fields/ApiFormField';
import { Thumbnail } from '../../components/images/Thumbnail';
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
import type { TableColumn } from '../Column';
import { NoteColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import { type RowAction, RowDeleteAction, RowEditAction } from '../RowActions';

/**
 * Construct a table listing related parts for a given part
 */
export function RelatedPartTable({
  partId
}: Readonly<{ partId: number }>): ReactNode {
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
        switchable: false,
        render: (record: any) => {
          const part = getPart(record);
          return (
            <Group
              wrap='nowrap'
              justify='left'
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
        accessor: 'ipn',
        title: t`IPN`,
        switchable: true,
        render: (record: any) => {
          const part = getPart(record);
          return part.IPN;
        }
      },
      {
        accessor: 'description',
        title: t`Part Description`,
        ellipsis: true,
        render: (record: any) => {
          return getPart(record).description;
        }
      },
      NoteColumn({})
    ];
  }, [partId]);

  const relatedPartFields: ApiFormFieldSet = useMemo(() => {
    return {
      part_1: {
        hidden: true
      },
      part_2: {},
      note: {}
    };
  }, []);

  const newRelatedPart = useCreateApiFormModal({
    url: ApiEndpoints.related_part_list,
    title: t`Add Related Part`,
    fields: relatedPartFields,
    initialData: {
      part_1: partId
    },
    table: table
  });

  const [selectedRelatedPart, setSelectedRelatedPart] = useState<
    number | undefined
  >(undefined);

  const deleteRelatedPart = useDeleteApiFormModal({
    url: ApiEndpoints.related_part_list,
    pk: selectedRelatedPart,
    title: t`Delete Related Part`,
    table: table
  });

  const editRelatedPart = useEditApiFormModal({
    url: ApiEndpoints.related_part_list,
    pk: selectedRelatedPart,
    title: t`Edit Related Part`,
    fields: {
      note: {}
    },
    table: table
  });

  const tableActions: ReactNode[] = useMemo(() => {
    return [
      <AddItemButton
        key='add-related-part'
        tooltip={t`Add Related Part`}
        hidden={!user.hasAddRole(UserRoles.part)}
        onClick={() => newRelatedPart.open()}
      />
    ];
  }, [user]);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.part),
          onClick: () => {
            setSelectedRelatedPart(record.pk);
            editRelatedPart.open();
          }
        }),
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
      {editRelatedPart.modal}
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
