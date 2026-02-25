import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import { t } from '@lingui/core/macro';
import { Table } from '@mantine/core';
import { useEffect, useMemo, useState } from 'react';
import { api } from '../App';
import RemoveRowButton from '../components/buttons/RemoveRowButton';
import type { TableFieldRowProps } from '../components/forms/fields/TableField';
import { RenderPart } from '../components/render/Part';
import { showApiErrorMessage } from '../functions/notifications';
import { useCreateApiFormModal } from '../hooks/UseForm';
import { useUserState } from '../states/UserState';

/**
 * Field set for BomItem form
 */
export function bomItemFields({
  showAssembly = false
}: {
  showAssembly?: boolean;
}): ApiFormFieldSet {
  return {
    part: {
      disabled: true,
      hidden: !showAssembly
    },
    sub_part: {
      filters: {
        active: true, // Only show active parts when creating a new BOM item
        component: true
      }
    },
    quantity: {},
    reference: {},
    setup_quantity: {},
    attrition: {},
    rounding_multiple: {},
    allow_variants: {},
    inherited: {},
    consumable: {},
    optional: {},
    note: {}
  };
}

function BomItemSubstituteRow({
  props,
  record
}: Readonly<{
  props: TableFieldRowProps;
  record: any;
}>) {
  const user = useUserState();

  return (
    <Table.Tr>
      <Table.Td>
        {record.part_detail && <RenderPart instance={record.part_detail} />}
      </Table.Td>
      <Table.Td>
        {user.hasDeleteRole(UserRoles.part) && (
          <RemoveRowButton
            onClick={() => {
              api
                .delete(apiUrl(ApiEndpoints.bom_substitute_list, record.pk))
                .then(() => {
                  props.removeFn(props.idx);
                })
                .catch((err) => {
                  showApiErrorMessage({
                    error: err,
                    title: t`Error`
                  });
                });
            }}
          />
        )}
      </Table.Td>
    </Table.Tr>
  );
}

type BomItemSubstituteFormProps = {
  bomItemId: number;
  bomItem: any;
  onClose?: () => void;
};

/**
 * Edit substitutes for a BOM item
 */
export function useEditBomSubstitutesForm(props: BomItemSubstituteFormProps) {
  const [substitutes, setSubstitutes] = useState<any[]>([]);

  useEffect(() => {
    setSubstitutes(props.bomItem?.substitutes ?? []);
  }, [props.bomItem.substitutes]);

  const formFields: ApiFormFieldSet = useMemo(() => {
    return {
      substitutes: {
        field_type: 'table',
        value: substitutes,
        ignore: true,
        modelRenderer: (row: TableFieldRowProps) => {
          const record = substitutes.find((r) => r.pk == row.item.pk);
          return record ? (
            <BomItemSubstituteRow props={row} record={record} />
          ) : null;
        },
        headers: [
          { title: t`Substitute Part`, style: { width: '100%' } },
          { title: '', style: { width: '50px' } }
        ]
      },
      bom_item: {
        hidden: true,
        value: props.bomItemId
      },
      part: {
        filters: {
          component: true
        }
      }
    };
  }, [props, substitutes]);

  return useCreateApiFormModal({
    title: t`Edit BOM Substitutes`,
    url: apiUrl(ApiEndpoints.bom_substitute_list),
    fields: formFields,
    initialData: {
      substitutes: substitutes
    },
    cancelText: t`Close`,
    submitText: t`Add Substitute`,
    successMessage: t`Substitute added`,
    onClose: () => {
      props.onClose?.();
    },
    checkClose: (response, form) => {
      // Keep the form open
      return false;
    },
    onFormSuccess(data, form) {
      // Add the new substitute to the list
      setSubstitutes((old) => [...old, data]);
      form.setValue('part', null);
      return false;
    }
  });
}
