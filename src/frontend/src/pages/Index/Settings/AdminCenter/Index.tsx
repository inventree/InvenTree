import { Trans, t } from '@lingui/macro';
import { Paper, SimpleGrid, Skeleton, Stack, Text, Title } from '@mantine/core';
import {
  IconClipboardCheck,
  IconCoins,
  IconCpu,
  IconDevicesPc,
  IconExclamationCircle,
  IconFileUpload,
  IconList,
  IconListDetails,
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

import PermissionDenied from '../../../../components/errors/PermissionDenied';
import { PlaceholderPill } from '../../../../components/items/Placeholder';
import PageTitle from '../../../../components/nav/PageTitle';
import { SettingsHeader } from '../../../../components/nav/SettingsHeader';
import type { PanelType } from '../../../../components/panels/Panel';
import { PanelGroup } from '../../../../components/panels/PanelGroup';
import { GlobalSettingList } from '../../../../components/settings/SettingList';
import { Loadable } from '../../../../functions/loading';
import { useUserState } from '../../../../states/UserState';

const ReportTemplatePanel = Loadable(
  lazy(() => import('./ReportTemplatePanel'))
);

const LabelTemplatePanel = Loadable(lazy(() => import('./LabelTemplatePanel')));

const UserManagementPanel = Loadable(
  lazy(() => import('./UserManagementPanel'))
);

const TaskManagementPanel = Loadable(
  lazy(() => import('./TaskManagementPanel'))
);

const CurrencyManagmentPanel = Loadable(
  lazy(() => import('./CurrencyManagmentPanel'))
);

const UnitManagmentPanel = Loadable(lazy(() => import('./UnitManagmentPanel')));

const PluginManagementPanel = Loadable(
  lazy(() => import('./PluginManagementPanel'))
);

const MachineManagementPanel = Loadable(
  lazy(() => import('./MachineManagementPanel'))
);

const PartParameterPanel = Loadable(lazy(() => import('./PartParameterPanel')));

const ErrorReportTable = Loadable(
  lazy(() => import('../../../../tables/settings/ErrorTable'))
);

const BarcodeScanHistoryTable = Loadable(
  lazy(() => import('../../../../tables/settings/BarcodeScanHistoryTable'))
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

const StocktakePanel = Loadable(lazy(() => import('./StocktakePanel')));

export default function AdminCenter() {
  const user = useUserState();

  const adminCenterPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'user',
        label: t`User Management`,
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
        content: <CurrencyManagmentPanel />
      },
      {
        name: 'projectcodes',
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
        name: 'customstates',
        label: t`Custom States`,
        icon: <IconListDetails />,
        content: <CustomStateTable />
      },
      {
        name: 'customunits',
        label: t`Custom Units`,
        icon: <IconScale />,
        content: <UnitManagmentPanel />
      },
      {
        name: 'part-parameters',
        label: t`Part Parameters`,
        icon: <IconList />,
        content: <PartParameterPanel />
      },
      {
        name: 'category-parameters',
        label: t`Category Parameters`,
        icon: <IconSitemap />,
        content: <PartCategoryTemplateTable />
      },
      {
        name: 'stocktake',
        label: t`Stocktake`,
        icon: <IconClipboardCheck />,
        content: <StocktakePanel />
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

  const QuickAction = () => (
    <Stack gap={'xs'} ml={'sm'}>
      <Title order={5}>
        <Trans>Quick Actions</Trans>
      </Title>
      <SimpleGrid cols={3}>
        <Paper shadow='xs' p='sm' withBorder>
          <Text>
            <Trans>Add a new user</Trans>
          </Text>
        </Paper>

        <Paper shadow='xs' p='sm' withBorder>
          <PlaceholderPill />
        </Paper>

        <Paper shadow='xs' p='sm' withBorder>
          <PlaceholderPill />
        </Paper>
      </SimpleGrid>
    </Stack>
  );

  if (!user.isLoggedIn()) {
    return <Skeleton />;
  }

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
          <QuickAction />
          <PanelGroup
            pageKey='admin-center'
            panels={adminCenterPanels}
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
