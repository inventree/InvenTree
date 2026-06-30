import { t } from '@lingui/core/macro';
import { Skeleton, Stack } from '@mantine/core';
import {
  IconBuildingWarehouse,
  IconInfoCircle,
  IconMap2,
  IconPackageExport,
  IconPackages,
  IconShoppingCart,
  IconTruckDelivery,
  IconTruckReturn,
  IconUsersGroup
} from '@tabler/icons-react';
import { type ReactNode, useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import type { PanelType } from '@lib/types/Panel';
import AdminButton from '../../components/buttons/AdminButton';
import { PrintingActions } from '../../components/buttons/PrintingActions';
import DetailsBadge from '../../components/details/DetailsBadge';
import {
  DeleteItemAction,
  EditItemAction,
  OptionsActionDropdown
} from '../../components/items/ActionDropdown';
import type { Breadcrumb } from '../../components/nav/BreadcrumbList';
import InstanceDetail from '../../components/nav/InstanceDetail';
import { PageDetail } from '../../components/nav/PageDetail';
import AttachmentPanel from '../../components/panels/AttachmentPanel';
import NotesPanel from '../../components/panels/NotesPanel';
import { PanelGroup } from '../../components/panels/PanelGroup';
import ParametersPanel from '../../components/panels/ParametersPanel';
import { companyFields } from '../../forms/CompanyForms';
import {
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { useUserState } from '../../states/UserState';
import { AddressTable } from '../../tables/company/AddressTable';
import { ContactTable } from '../../tables/company/ContactTable';
import { ManufacturerPartTable } from '../../tables/purchasing/ManufacturerPartTable';
import { PurchaseOrderTable } from '../../tables/purchasing/PurchaseOrderTable';
import { SupplierPartTable } from '../../tables/purchasing/SupplierPartTable';
import { ReturnOrderTable } from '../../tables/sales/ReturnOrderTable';
import { SalesOrderTable } from '../../tables/sales/SalesOrderTable';
import { StockItemTable } from '../../tables/stock/StockItemTable';
import { CompanyDetailsPanel } from './CompanyDetailsPanel';

export type CompanyDetailProps = {
  title: string;
  breadcrumbs: Breadcrumb[];
  last_crumb_url: string;
};

/**
 * Detail view for a single company instance
 */
export default function CompanyDetail(props: Readonly<CompanyDetailProps>) {
  const { id } = useParams();

  const navigate = useNavigate();
  const user = useUserState();

  const {
    instance: company,
    refreshInstance,
    instanceQuery
  } = useInstance({
    endpoint: ApiEndpoints.company_list,
    pk: id,
    params: {
      tags: true
    },
    refetchOnMount: true
  });

  const detailsPanel = instanceQuery.isFetching ? (
    <Skeleton />
  ) : (
    <CompanyDetailsPanel
      instance={company}
      allowImageEdit
      refreshInstance={refreshInstance}
    />
  );

  const companyPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'details',
        label: t`Company Details`,
        icon: <IconInfoCircle />,
        content: detailsPanel
      },
      {
        name: 'supplied-parts',
        label: t`Supplied Parts`,
        icon: <IconPackageExport />,
        hidden: !company?.is_supplier,
        content: company?.pk && <SupplierPartTable supplierId={company.pk} />
      },
      {
        name: 'manufactured-parts',
        label: t`Manufactured Parts`,
        icon: <IconBuildingWarehouse />,
        hidden: !company?.is_manufacturer,
        content: company?.pk && (
          <ManufacturerPartTable manufacturerId={company.pk} />
        )
      },
      {
        name: 'purchase-orders',
        label: t`Purchase Orders`,
        icon: <IconShoppingCart />,
        hidden: !company?.is_supplier,
        content: company?.pk && <PurchaseOrderTable supplierId={company.pk} />
      },
      {
        name: 'stock-items',
        label: t`Stock Items`,
        icon: <IconPackages />,
        hidden: !company?.is_manufacturer && !company?.is_supplier,
        content: company?.pk && (
          <StockItemTable
            allowAdd={false}
            tableName='company-stock'
            params={{ company: company.pk }}
          />
        )
      },
      {
        name: 'sales-orders',
        label: t`Sales Orders`,
        icon: <IconTruckDelivery />,
        hidden: !company?.is_customer,
        content: company?.pk && <SalesOrderTable customerId={company.pk} />
      },
      {
        name: 'return-orders',
        label: t`Return Orders`,
        icon: <IconTruckReturn />,
        hidden: !company?.is_customer,
        content: company.pk ? (
          <ReturnOrderTable customerId={company.pk} />
        ) : (
          <Skeleton />
        )
      },
      {
        name: 'assigned-stock',
        label: t`Assigned Stock`,
        icon: <IconPackageExport />,
        hidden: !company?.is_customer,
        content: company?.pk ? (
          <StockItemTable
            allowAdd={false}
            tableName='assigned-stock'
            showLocation={false}
            allowReturn
            defaultInStock={null}
            params={{ customer: company.pk }}
          />
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
      ParametersPanel({
        model_type: ModelType.company,
        model_id: company?.pk
      }),
      AttachmentPanel({
        model_type: ModelType.company,
        model_id: company.pk
      }),
      NotesPanel({
        model_type: ModelType.company,
        model_id: company.pk,
        has_note: !!company.notes
      })
    ];
  }, [id, company, user]);

  const editCompany = useEditApiFormModal({
    url: ApiEndpoints.company_list,
    pk: company?.pk,
    title: t`Edit Company`,
    fields: companyFields(),
    queryParams: new URLSearchParams({ tags: 'true' }),
    onFormSuccess: refreshInstance
  });

  const deleteCompany = useDeleteApiFormModal({
    url: ApiEndpoints.company_list,
    pk: company?.pk,
    title: t`Delete Company`,
    onFormSuccess: () => {
      navigate('/');
    }
  });

  const companyActions = useMemo(() => {
    return [
      <AdminButton model={ModelType.company} id={company.pk} />,
      <PrintingActions
        modelType={ModelType.company}
        items={[company.pk]}
        enableReports
      />,
      <OptionsActionDropdown
        tooltip={t`Company Actions`}
        actions={[
          EditItemAction({
            hidden: !user.hasChangeRole(UserRoles.purchase_order),
            onClick: () => editCompany.open()
          }),
          DeleteItemAction({
            hidden: !user.hasDeleteRole(UserRoles.purchase_order),
            onClick: () => deleteCompany.open()
          })
        ]}
      />
    ];
  }, [id, company, user]);

  const badges: ReactNode[] = useMemo(() => {
    return [
      <DetailsBadge
        label={t`Inactive`}
        color='red'
        visible={company.active == false}
      />
    ];
  }, [company]);

  return (
    <>
      {editCompany.modal}
      {deleteCompany.modal}
      <InstanceDetail
        query={instanceQuery}
        requiredPermission={ModelType.company}
      >
        <Stack gap='xs'>
          <PageDetail
            title={`${t`Company`}: ${company.name}`}
            subtitle={company.description}
            actions={companyActions}
            imageUrl={company.image}
            breadcrumbs={props.breadcrumbs}
            lastCrumb={[
              {
                name: company.name,
                url: `${props.last_crumb_url}/${company.pk}/`
              }
            ]}
            badges={badges}
            editAction={editCompany.open}
            editEnabled={user.hasChangePermission(ModelType.company)}
          />
          <PanelGroup
            pageKey='company'
            panels={companyPanels}
            instance={company}
            reloadInstance={refreshInstance}
            model={ModelType.company}
            id={company.pk}
          />
        </Stack>
      </InstanceDetail>
    </>
  );
}
