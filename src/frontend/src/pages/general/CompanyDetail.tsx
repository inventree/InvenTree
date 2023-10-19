import { t } from '@lingui/macro';
import { LoadingOverlay, Stack } from '@mantine/core';
import {
  IconBuildingFactory2,
  IconBuildingWarehouse,
  IconInfoCircle,
  IconMap2,
  IconNotes,
  IconPackageExport,
  IconPackages,
  IconPaperclip,
  IconShoppingCart,
  IconTruckDelivery,
  IconTruckReturn,
  IconUsersGroup
} from '@tabler/icons-react';
import { useMemo } from 'react';
import { useParams } from 'react-router-dom';

import { PanelGroup } from '../../components/nav/PanelGroup';
import { PanelType } from '../../components/nav/PanelGroup';
import { AttachmentTable } from '../../components/tables/general/AttachmentTable';
import { NotesEditor } from '../../components/widgets/MarkdownEditor';
import { useInstance } from '../../hooks/UseInstance';
import { ApiPaths, apiUrl } from '../../states/ApiState';

/**
 * Detail view for a single company instance
 */
export default function CompanyDetail() {
  const { id } = useParams();

  const {
    instance: company,
    refreshInstance,
    instanceQuery
  } = useInstance({
    endpoint: ApiPaths.company_list,
    pk: id,
    params: {},
    refetchOnMount: true
  });

  const companyPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'details',
        label: t`Details`,
        icon: <IconInfoCircle />
      },
      {
        name: 'manufactured-parts',
        label: t`Manufactured Parts`,
        icon: <IconBuildingFactory2 />,
        hidden: !company?.is_manufacturer
      },
      {
        name: 'supplied-parts',
        label: t`Supplied Parts`,
        icon: <IconBuildingWarehouse />,
        hidden: !company?.is_supplier
      },
      {
        name: 'purchase-orders',
        label: t`Purchase Orders`,
        icon: <IconShoppingCart />,
        hidden: !company?.is_supplier
      },
      {
        name: 'stock-items',
        label: t`Stock Items`,
        icon: <IconPackages />,
        hidden: !company?.is_manufacturer && !company?.is_supplier
      },
      {
        name: 'sales-orders',
        label: t`Sales Orders`,
        icon: <IconTruckDelivery />,
        hidden: !company?.is_customer
      },
      {
        name: 'return-orders',
        label: t`Return Orders`,
        icon: <IconTruckReturn />,
        hidden: !company?.is_customer
      },
      {
        name: 'assigned-stock',
        label: t`Assigned Stock`,
        icon: <IconPackageExport />,
        hidden: !company?.is_customer
      },
      {
        name: 'contacts',
        label: t`Contacts`,
        icon: <IconUsersGroup />
      },
      {
        name: 'addresses',
        label: t`Addresses`,
        icon: <IconMap2 />
      },
      {
        name: 'attachments',
        label: t`Attachments`,
        icon: <IconPaperclip />,
        content: (
          <AttachmentTable
            endpoint={ApiPaths.company_attachment_list}
            model="company"
            pk={company.pk ?? -1}
          />
        )
      },
      {
        name: 'notes',
        label: t`Notes`,
        icon: <IconNotes />,
        content: (
          <NotesEditor
            url={apiUrl(ApiPaths.company_list, company.pk)}
            data={company?.notes ?? ''}
            allowEdit={true}
          />
        )
      }
    ];
  }, [id, company]);

  return (
    <Stack spacing="xs">
      <LoadingOverlay visible={instanceQuery.isFetching} />
      <PanelGroup pageKey="company" panels={companyPanels} />
    </Stack>
  );
}
