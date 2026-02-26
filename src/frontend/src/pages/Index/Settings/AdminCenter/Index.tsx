import { t } from '@lingui/core/macro';
import { Stack } from '@mantine/core';
import {
  IconCoins,
  IconCpu,
  IconDevicesPc,
  IconExclamationCircle,
  IconFileDownload,
  IconFileUpload,
  IconHome,
  IconList,
  IconListDetails,
  IconMail,
  IconPackages,
  IconPlugConnected,
  IconQrcode,
  IconReport,
  IconScale,
  IconSitemap,
  IconTags,
  IconUsersGroup
} from '@tabler/icons-react';
import { lazy, useMemo } from 'react';

import { UserRoles } from '@lib/enums/Roles';
import PermissionDenied from '../../../../components/errors/PermissionDenied';
import PageTitle from '../../../../components/nav/PageTitle';
import { SettingsHeader } from '../../../../components/nav/SettingsHeader';
import type {
  PanelGroupType,
  PanelType
} from '../../../../components/panels/Panel';
import { PanelGroup } from '../../../../components/panels/PanelGroup';
import { GlobalSettingList } from '../../../../components/settings/SettingList';
import { Loadable } from '../../../../functions/loading';
import { useUserState } from '../../../../states/UserState';

const ReportTemplatePanel = Loadable(
  lazy(() => import('./ReportTemplatePanel'))
);

const LabelTemplatePanel = Loadable(lazy(() => import('./LabelTemplatePanel')));

const HomePanel = Loadable(lazy(() => import('./HomePanel')));

const UserManagementPanel = Loadable(
  lazy(() => import('./UserManagementPanel'))
);

const EmailManagementPanel = Loadable(
  lazy(() => import('./EmailManagementPanel'))
);

const TaskManagementPanel = Loadable(
  lazy(() => import('./TaskManagementPanel'))
);

const CurrencyManagementPanel = Loadable(
  lazy(() => import('./CurrencyManagementPanel'))
);

const UnitManagementPanel = Loadable(
  lazy(() => import('./UnitManagementPanel'))
);

const PluginManagementPanel = Loadable(
  lazy(() => import('./PluginManagementPanel'))
);

const MachineManagementPanel = Loadable(
  lazy(() => import('./MachineManagementPanel'))
);

const ParameterPanel = Loadable(lazy(() => import('./ParameterPanel')));

const ErrorReportTable = Loadable(
  lazy(() => import('../../../../tables/settings/ErrorTable'))
);

const BarcodeScanHistoryTable = Loadable(
  lazy(() => import('../../../../tables/settings/BarcodeScanHistoryTable'))
);

const ExportSessionTable = Loadable(
  lazy(() => import('../../../../tables/settings/ExportSessionTable'))
);

const ImportSessionTable = Loadable(
  lazy(() => import('../../../../tables/settings/ImportSessionTable'))
);

const ProjectCodeTable = Loadable(
  lazy(() => import('../../../../tables/settings/ProjectCodeTable'))
);

const CustomStateTable = Loadable(
  lazy(() => import('../../../../tables/settings/CustomStateTable'))
);

const PartCategoryTemplateTable = Loadable(
  lazy(() => import('../../../../tables/part/PartCategoryTemplateTable'))
);

const LocationTypesTable = Loadable(
  lazy(() => import('../../../../tables/stock/LocationTypesTable'))
);

export default function AdminCenter() {
  const user = useUserState();

  const adminCenterPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'home',
        label: t`Home`,
        icon: <IconHome />,
        content: <HomePanel />,
        showHeadline: false
      },
      {
        name: 'user',
        label: t`Users / Access`,
        icon: <IconUsersGroup />,
        content: <UserManagementPanel />,
        hidden: !user.hasViewRole(UserRoles.admin)
      },
      {
        name: 'email',
        label: t`Email Settings`,
        icon: <IconMail />,
        content: <EmailManagementPanel />,
        hidden: !user.isSuperuser()
      },
      {
        name: 'import',
        label: t`Data Import`,
        icon: <IconFileUpload />,
        content: <ImportSessionTable />
      },
      {
        name: 'export',
        label: t`Data Export`,
        icon: <IconFileDownload />,
        content: <ExportSessionTable />
      },
      {
        name: 'barcode-history',
        label: t`Barcode Scans`,
        icon: <IconQrcode />,
        content: <BarcodeScanHistoryTable />
      },
      {
        name: 'background',
        label: t`Background Tasks`,
        icon: <IconCpu />,
        content: <TaskManagementPanel />
      },
      {
        name: 'errors',
        label: t`Error Reports`,
        icon: <IconExclamationCircle />,
        content: <ErrorReportTable />
      },
      {
        name: 'currencies',
        label: t`Currencies`,
        icon: <IconCoins />,
        content: <CurrencyManagementPanel />
      },
      {
        name: 'project-codes',
        label: t`Project Codes`,
        icon: <IconListDetails />,
        content: (
          <Stack gap='xs'>
            <GlobalSettingList keys={['PROJECT_CODES_ENABLED']} />
            <ProjectCodeTable />
          </Stack>
        )
      },
      {
        name: 'custom-states',
        label: t`Custom States`,
        icon: <IconListDetails />,
        content: <CustomStateTable />
      },
      {
        name: 'custom-units',
        label: t`Custom Units`,
        icon: <IconScale />,
        content: <UnitManagementPanel />
      },
      {
        name: 'parameters',
        label: t`Parameters`,
        icon: <IconList />,
        content: <ParameterPanel />,
        hidden: !user.hasViewRole(UserRoles.part)
      },
      {
        name: 'category-parameters',
        label: t`Category Parameters`,
        icon: <IconSitemap />,
        content: <PartCategoryTemplateTable />,
        hidden: !user.hasViewRole(UserRoles.part_category)
      },
      {
        name: 'labels',
        label: t`Label Templates`,
        icon: <IconTags />,
        content: <LabelTemplatePanel />
      },
      {
        name: 'reports',
        label: t`Report Templates`,
        icon: <IconReport />,
        content: <ReportTemplatePanel />
      },
      {
        name: 'location-types',
        label: t`Location Types`,
        icon: <IconPackages />,
        content: <LocationTypesTable />,
        hidden: !user.hasViewRole(UserRoles.stock_location)
      },
      {
        name: 'plugin',
        label: t`Plugins`,
        icon: <IconPlugConnected />,
        content: <PluginManagementPanel />,
        hidden: !user.hasViewRole(UserRoles.admin)
      },
      {
        name: 'machine',
        label: t`Machines`,
        icon: <IconDevicesPc />,
        content: <MachineManagementPanel />,
        hidden: !user.hasViewRole(UserRoles.admin)
      }
    ];
  }, [user]);
  const grouping: PanelGroupType[] = useMemo(() => {
    return [
      { id: 'home', label: '', panelIDs: ['home'] },
      {
        id: 'ops',
        label: t`Operations`,
        panelIDs: [
          'user',
          'barcode-history',
          'background',
          'errors',
          'currencies',
          'email'
        ]
      },
      {
        id: 'data',
        label: t`Data Management`,
        panelIDs: [
          'import',
          'export',
          'project-codes',
          'custom-states',
          'custom-units'
        ]
      },
      {
        id: 'reporting',
        label: t`Reporting`,
        panelIDs: ['labels', 'reports']
      },
      {
        id: 'plm',
        label: t`PLM`,
        panelIDs: [
          'parameters',
          'category-parameters',
          'location-types',
          'stocktake'
        ]
      },
      {
        id: 'extend',
        label: t`Extend / Integrate`,
        panelIDs: ['plugin', 'machine']
      }
    ];
  }, []);

  return (
    <>
      <PageTitle title={t`Admin Center`} />
      {user.isStaff() ? (
        <Stack gap='xs'>
          <SettingsHeader
            label='admin'
            title={t`Admin Center`}
            subtitle={t`Advanced Options`}
          />
          <PanelGroup
            pageKey='admin-center'
            panels={adminCenterPanels}
            groups={grouping}
            collapsible={true}
            model='admincenter'
            id={null}
          />
        </Stack>
      ) : (
        <PermissionDenied />
      )}
    </>
  );
}
