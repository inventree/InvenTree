import { t } from '@lingui/macro';
import { Group, LoadingOverlay, Stack, Text } from '@mantine/core';
import {
  IconBuildingFactory2,
  IconBuildingWarehouse,
  IconDots,
  IconEdit,
  IconInfoCircle,
  IconMap2,
  IconNotes,
  IconPackageExport,
  IconPackages,
  IconPaperclip,
  IconShoppingCart,
  IconTrash,
  IconTruckDelivery,
  IconTruckReturn,
  IconUsersGroup
} from '@tabler/icons-react';
import { useMemo } from 'react';
import { useParams } from 'react-router-dom';

import { Thumbnail } from '../../components/images/Thumbnail';
import { ActionDropdown } from '../../components/items/ActionDropdown';
import { Breadcrumb } from '../../components/nav/BreadcrumbList';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup } from '../../components/nav/PanelGroup';
import { PanelType } from '../../components/nav/PanelGroup';
import { AttachmentTable } from '../../components/tables/general/AttachmentTable';
import { PurchaseOrderTable } from '../../components/tables/purchasing/PurchaseOrderTable';
import { ReturnOrderTable } from '../../components/tables/sales/ReturnOrderTable';
import { SalesOrderTable } from '../../components/tables/sales/SalesOrderTable';
import { StockItemTable } from '../../components/tables/stock/StockItemTable';
import { NotesEditor } from '../../components/widgets/MarkdownEditor';
import { editCompany } from '../../functions/forms/CompanyForms';
import { useInstance } from '../../hooks/UseInstance';
import { ApiPaths, apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';

export type CompanyDetailProps = {
  title: string;
  breadcrumbs: Breadcrumb[];
};

/**
 * Detail view for a single company instance
 */
export default function CompanyDetail(props: CompanyDetailProps) {
  const { id } = useParams();

  const user = useUserState();

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
        hidden: !company?.is_supplier,
        content: company?.pk && (
          <PurchaseOrderTable params={{ supplier: company.pk }} />
        )
      },
      {
        name: 'stock-items',
        label: t`Stock Items`,
        icon: <IconPackages />,
        hidden: !company?.is_manufacturer && !company?.is_supplier,
        content: company?.pk && (
          <StockItemTable params={{ company: company.pk }} />
        )
      },
      {
        name: 'sales-orders',
        label: t`Sales Orders`,
        icon: <IconTruckDelivery />,
        hidden: !company?.is_customer,
        content: company?.pk && (
          <SalesOrderTable params={{ customer: company.pk }} />
        )
      },
      {
        name: 'return-orders',
        label: t`Return Orders`,
        icon: <IconTruckReturn />,
        hidden: !company?.is_customer,
        content: company.pk && (
          <ReturnOrderTable params={{ customer: company.pk }} />
        )
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

  const companyDetail = useMemo(() => {
    return (
      <Group spacing="xs" noWrap={true}>
        <Thumbnail
          src={String(company.image || '')}
          size={128}
          alt={company?.name}
        />
        <Stack spacing="xs">
          <Text size="lg" weight={500}>
            {company.name}
          </Text>
          <Text size="sm">{company.description}</Text>
        </Stack>
      </Group>
    );
  }, [id, company]);

  const companyActions = useMemo(() => {
    // TODO: Finer fidelity on these permissions, perhaps?
    let canEdit = user.checkUserRole('purchase_order', 'change');
    let canDelete = user.checkUserRole('purchase_order', 'delete');

    return [
      <ActionDropdown
        tooltip={t`Company Actions`}
        icon={<IconDots />}
        actions={[
          {
            icon: <IconEdit color="blue" />,
            name: t`Edit`,
            tooltip: t`Edit company`,
            disabled: !canEdit,
            onClick: () => {
              if (company?.pk) {
                editCompany({
                  pk: company?.pk,
                  callback: refreshInstance
                });
              }
            }
          },
          {
            icon: <IconTrash color="red" />,
            name: t`Delete`,
            tooltip: t`Delete company`,
            disabled: !canDelete
          }
        ]}
      />
    ];
  }, [id, company, user]);

  return (
    <Stack spacing="xs">
      <LoadingOverlay visible={instanceQuery.isFetching} />
      <PageDetail
        detail={companyDetail}
        actions={companyActions}
        breadcrumbs={props.breadcrumbs}
      />
      <PanelGroup pageKey="company" panels={companyPanels} />
    </Stack>
  );
}
