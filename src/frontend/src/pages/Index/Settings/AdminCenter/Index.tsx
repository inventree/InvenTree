import { t } from '@lingui/macro';
import { Divider, Skeleton, Stack } from '@mantine/core';
import {
  IconCoins,
  IconCpu,
  IconDevicesPc,
  IconExclamationCircle,
  IconFileUpload,
  IconHome,
  IconList,
  IconListDetails,
  IconPackages,
  IconPlugConnected,
  IconReport,
  IconScale,
  IconSitemap,
  IconTags,
  IconUsersGroup
} from '@tabler/icons-react';
import { lazy, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

import PermissionDenied from '../../../../components/errors/PermissionDenied';
import { PanelGroup, PanelType } from '../../../../components/nav/PanelGroup';
import { SettingsHeader } from '../../../../components/nav/SettingsHeader';
import { QuickAction } from '../../../../components/settings/QuickAction';
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

const TaskManagementPanel = Loadable(
  lazy(() => import('./TaskManagementPanel'))
);

const CurrencyManagmentPanel = Loadable(
  lazy(() => import('./CurrencyManagmentPanel'))
);

const PluginManagementPanel = Loadable(
  lazy(() => import('./PluginManagementPanel'))
);

const MachineManagementPanel = Loadable(
  lazy(() => import('./MachineManagementPanel'))
);

const ErrorReportTable = Loadable(
  lazy(() => import('../../../../tables/settings/ErrorTable'))
);

const ImportSesssionTable = Loadable(
  lazy(() => import('../../../../tables/settings/ImportSessionTable'))
);

const ProjectCodeTable = Loadable(
  lazy(() => import('../../../../tables/settings/ProjectCodeTable'))
);

const CustomStateTable = Loadable(
  lazy(() => import('../../../../tables/settings/CustomStateTable'))
);

const CustomUnitsTable = Loadable(
  lazy(() => import('../../../../tables/settings/CustomUnitsTable'))
);

const PartParameterTemplateTable = Loadable(
  lazy(() => import('../../../../tables/part/PartParameterTemplateTable'))
);

const PartCategoryTemplateTable = Loadable(
  lazy(() => import('../../../../tables/part/PartCategoryTemplateTable'))
);

const LocationTypesTable = Loadable(
  lazy(() => import('../../../../tables/stock/LocationTypesTable'))
);

export default function AdminCenter() {
  const user = useUserState();
  const navigate = useNavigate();
  const location = useLocation();

  const panel = useMemo(() => {
    return location.pathname.replace('/settings/admin/', '');
  }, [location.pathname]);
  const showQuickAction: boolean = useMemo(() => {
    return panel !== 'home';
  }, [panel]);

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
        label: t`Users`,
        icon: <IconUsersGroup />,
        content: <UserManagementPanel />
      },
      {
        name: 'import',
        label: t`Data Import`,
        icon: <IconFileUpload />,
        content: <ImportSesssionTable />
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
        content: <CurrencyManagmentPanel />
      },
      {
        name: 'projectcodes',
        label: t`Project Codes`,
        icon: <IconListDetails />,
        content: (
          <Stack gap="xs">
            <GlobalSettingList keys={['PROJECT_CODES_ENABLED']} />
            <Divider />
            <ProjectCodeTable />
          </Stack>
        )
      },
      {
        name: 'customstates',
        label: t`Custom States`,
        icon: <IconListDetails />,
        content: <CustomStateTable />
      },
      {
        name: 'customunits',
        label: t`Custom Units`,
        icon: <IconScale />,
        content: <CustomUnitsTable />
      },
      {
        name: 'part-parameters',
        label: t`Part Parameters`,
        icon: <IconList />,
        content: <PartParameterTemplateTable />
      },
      {
        name: 'category-parameters',
        label: t`Category Parameters`,
        icon: <IconSitemap />,
        content: <PartCategoryTemplateTable />
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
        content: <LocationTypesTable />
      },
      {
        name: 'plugin',
        label: t`Plugins`,
        icon: <IconPlugConnected />,
        content: <PluginManagementPanel />
      },
      {
        name: 'machine',
        label: t`Machines`,
        icon: <IconDevicesPc />,
        content: <MachineManagementPanel />
      }
    ];
  }, []);

  if (!user.isLoggedIn()) {
    return <Skeleton />;
  }

  return (
    <>
      {user.isStaff() ? (
        <Stack gap="xs">
          <SettingsHeader
            title={t`Admin Center`}
            subtitle={t`Advanced Options`}
            switch_link="/settings/system"
            switch_text="System Settings"
          />
          {showQuickAction ? <QuickAction navigate={navigate} /> : null}
          <PanelGroup
            pageKey="admin-center"
            panels={adminCenterPanels}
            collapsible={true}
            ml={'sm'}
          />
        </Stack>
      ) : (
        <PermissionDenied />
      )}
    </>
  );
}
