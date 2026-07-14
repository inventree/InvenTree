import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import {
  IconFileUpload,
  IconPackageImport,
  IconPlus
} from '@tabler/icons-react';
import { useMemo, useRef } from 'react';
import { ActionDropdown } from '../../components/items/ActionDropdown';
import ImportPartWizard from '../../components/wizards/ImportPartWizard';
import { dataImporterSessionFields } from '../../forms/ImporterForms';
import { usePartFields } from '../../forms/PartForms';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { usePluginsWithMixin } from '../../hooks/UsePlugins';
import { openGlobalImporter } from '../../states/ImporterState';
import { useUserState } from '../../states/UserState';
import {
  DescriptionColumn,
  PartColumn
} from '../ColumnRenderers';
import ParametricDataTable from '../general/ParametricDataTable';
import { PartTableFilters } from './PartTableFilters';

export default function ParametricPartTable({
  categoryId,
  enableImport = true
}: Readonly<{
  categoryId?: any;
  enableImport?: boolean;
}>) {
  const user = useUserState();
  const tableRefreshRef = useRef<() => void>(() => {});

  const customFilters: TableFilter[] = useMemo(() => PartTableFilters(), []);

  const customColumns: TableColumn[] = useMemo(() => {
    return [
      PartColumn({
        part: '',
        switchable: false
      }),
      DescriptionColumn({
        defaultVisible: false
      }),
      {
        accessor: 'IPN',
        sortable: true,
        defaultVisible: false
      },
      {
        accessor: 'total_in_stock',
        sortable: true
      }
    ];
  }, []);

  const importSessionFields = useMemo(() => {
    const fields = dataImporterSessionFields({
      modelType: ModelType.part
    });

    fields.field_defaults.value = {
      category: categoryId
    };

    return fields;
  }, [categoryId]);

  const importParts = useCreateApiFormModal({
    url: ApiEndpoints.import_session_list,
    title: t`Import Parts`,
    fields: importSessionFields,
    onFormSuccess: (response: any) => {
      openGlobalImporter(response.pk, { onClose: tableRefreshRef.current });
    }
  });

  const initialPartData = useMemo(() => {
    return { category: categoryId };
  }, [categoryId]);

  const newPartFields = usePartFields({ create: true });

  const newPart = useCreateApiFormModal({
    url: ApiEndpoints.part_list,
    title: t`Add Part`,
    fields: newPartFields,
    initialData: initialPartData,
    follow: true,
    modelType: ModelType.part,
    keepOpenOption: true
  });

  const supplierPlugins = usePluginsWithMixin('supplier');
  const importPartWizard = ImportPartWizard({ categoryId });

  const tableActions = useMemo(() => {
    return [
      <ActionDropdown
        key='add-parts-actions'
        tooltip={t`Add Parts`}
        position='bottom-start'
        icon={<IconPlus />}
        hidden={!user.hasAddRole(UserRoles.part)}
        actions={[
          {
            name: t`Create Part`,
            icon: <IconPlus />,
            tooltip: t`Create a new part`,
            onClick: () => newPart.open()
          },
          {
            name: t`Import from File`,
            icon: <IconFileUpload />,
            tooltip: t`Import parts from a file`,
            onClick: () => importParts.open(),
            hidden: !enableImport
          },
          {
            name: t`Import from Supplier`,
            icon: <IconPackageImport />,
            tooltip: t`Import parts from a supplier plugin`,
            hidden: !enableImport || supplierPlugins.length === 0,
            onClick: () => importPartWizard.openWizard()
          }
        ]}
      />
    ];
  }, [
    user,
    enableImport,
    supplierPlugins,
    newPart.open,
    importParts.open,
    importPartWizard.openWizard
  ]);

  return (
    <>
      {newPart.modal}
      {importParts.modal}
      {importPartWizard.wizard}
      <ParametricDataTable
        modelType={ModelType.part}
        relatedModel={'category'}
        relatedModelId={categoryId}
        endpoint={ApiEndpoints.part_list}
        customColumns={customColumns}
        customFilters={customFilters}
        customActions={tableActions}
        refreshRef={tableRefreshRef}
        queryParams={{
          category: categoryId,
          cascade: true,
          category_detail: true
        }}
      />
    </>
  );
}
