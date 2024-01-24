import { t } from '@lingui/macro';
import { LoadingOverlay, Skeleton, Stack } from '@mantine/core';
import {
  IconBuildingFactory2,
  IconBuildingWarehouse,
  IconDots,
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

import {
  ActionDropdown,
  DeleteItemAction,
  EditItemAction
} from '../../components/items/ActionDropdown';
import { Breadcrumb } from '../../components/nav/BreadcrumbList';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup } from '../../components/nav/PanelGroup';
import { PanelType } from '../../components/nav/PanelGroup';
import { AddressTable } from '../../components/tables/company/AddressTable';
import { ContactTable } from '../../components/tables/company/ContactTable';
import { AttachmentTable } from '../../components/tables/general/AttachmentTable';
import { ManufacturerPartTable } from '../../components/tables/purchasing/ManufacturerPartTable';
import { PurchaseOrderTable } from '../../components/tables/purchasing/PurchaseOrderTable';
import { SupplierPartTable } from '../../components/tables/purchasing/SupplierPartTable';
import { ReturnOrderTable } from '../../components/tables/sales/ReturnOrderTable';
import { SalesOrderTable } from '../../components/tables/sales/SalesOrderTable';
import { StockItemTable } from '../../components/tables/stock/StockItemTable';
import { NotesEditor } from '../../components/widgets/MarkdownEditor';
import { ApiPaths } from '../../enums/ApiEndpoints';
import { UserRoles } from '../../enums/Roles';
import { editCompany } from '../../forms/CompanyForms';
import { useInstance } from '../../hooks/UseInstance';
import { apiUrl } from '../../states/ApiState';
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
        hidden: !company?.is_manufacturer,
        content: company?.pk && (
          <ManufacturerPartTable params={{ manufacturer: company.pk }} />
        )
      },
      {
        name: 'supplied-parts',
        label: t`Supplied Parts`,
        icon: <IconBuildingWarehouse />,
        hidden: !company?.is_supplier,
        content: company?.pk && (
          <SupplierPartTable params={{ supplier: company.pk }} />
        )
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
        hidden: !company?.is_customer,
        content: company?.pk ? (
          <StockItemTable params={{ customer: company.pk }} />
        ) : (
          <Skeleton />
        )
      },
      {
        name: 'contacts',
        label: t`Contacts`,
        icon: <IconUsersGroup />,
        content: company?.pk && <ContactTable companyId={company.pk} />
      },
      {
        name: 'addresses',
        label: t`Addresses`,
        icon: <IconMap2 />,
        content: company?.pk && <AddressTable companyId={company.pk} />
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

  const companyActions = useMemo(() => {
    return [
      <ActionDropdown
        key="company"
        tooltip={t`Company Actions`}
        icon={<IconDots />}
        actions={[
          EditItemAction({
            disabled: !user.hasChangeRole(UserRoles.purchase_order),
            onClick: () => {
              if (company?.pk) {
                editCompany({
                  pk: company?.pk,
                  callback: refreshInstance
                });
              }
            }
          }),
          DeleteItemAction({
            disabled: !user.hasDeleteRole(UserRoles.purchase_order)
          })
        ]}
      />
    ];
  }, [id, company, user]);

  return (
    <Stack spacing="xs">
      <LoadingOverlay visible={instanceQuery.isFetching} />
      <PageDetail
        title={t`Company` + `: ${company.name}`}
        subtitle={company.description}
        actions={companyActions}
        imageUrl={company.image}
        breadcrumbs={props.breadcrumbs}
      />
      <PanelGroup pageKey="company" panels={companyPanels} />
    </Stack>
  );
}
