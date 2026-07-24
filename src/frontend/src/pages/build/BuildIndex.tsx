import type { EventContentArg } from '@fullcalendar/core';
import { ModelType, PluginPanelKey } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import type { TableFilter } from '@lib/types/Filters';
import type { PanelType } from '@lib/types/Panel';
import { t } from '@lingui/core/macro';
import { Stack } from '@mantine/core';
import { useLocalStorage } from '@mantine/hooks';
import {
  IconCalendar,
  IconListDetails,
  IconTable,
  IconTools
} from '@tabler/icons-react';
import { useCallback, useMemo } from 'react';
import OrderCalendar from '../../components/calendar/OrderCalendar';
import OrderCalendarToolTip from '../../components/calendar/OrderCalendarToolTip';
import PermissionDenied from '../../components/errors/PermissionDenied';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup } from '../../components/panels/PanelGroup';
import SegmentedControlPanel from '../../components/panels/SegmentedControlPanel';
import { useGlobalSettingsState } from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';
import BuildOrderFilters from '../../tables/build/BuildOrderFilters';
import BuildOrderParametricTable from '../../tables/build/BuildOrderParametricTable';
import { BuildOrderTable } from '../../tables/build/BuildOrderTable';

function BuildOrderCalendar() {
  const globalSettings = useGlobalSettingsState();

  const calendarFilters: TableFilter[] = useMemo(() => {
    return BuildOrderFilters({
      includeDateFilters: false,
      externalBuilds: globalSettings.isSet('BUILDORDER_EXTERNAL_BUILDS')
    });
  }, [globalSettings]);

  const renderTooltip = useCallback((event: EventContentArg) => {
    const order = event?.event?._def?.extendedProps?.order;

    const extraEntries: { label: string; value: string | React.ReactNode }[] =
      [];

    if (order?.quantity) {
      extraEntries.push({
        label: t`Quantity`,
        value: order.quantity
      });
    }

    return OrderCalendarToolTip({
      event: event,
      modelType: ModelType.part,
      instanceLookup: 'part_detail',
      extraEntries: extraEntries
    });
  }, []);

  return (
    <OrderCalendar
      model={ModelType.build}
      role={UserRoles.build}
      params={{ part_detail: true }}
      filters={calendarFilters}
      initialFilters={[{ name: 'outstanding', value: 'true' }]}
      tooltip={renderTooltip}
    />
  );
}

/**
 * Build Order index page
 */
export default function BuildIndex() {
  const user = useUserState();

  const [buildOrderView, setBuildOrderView] = useLocalStorage<string>({
    key: 'build-order-view',
    defaultValue: 'table'
  });

  const panels: PanelType[] = useMemo(() => {
    return [
      SegmentedControlPanel({
        name: 'buildorder',
        label: t`Build Orders`,
        icon: <IconTools />,
        selection: buildOrderView,
        onChange: setBuildOrderView,
        options: [
          {
            value: 'table',
            label: t`Table View`,
            icon: <IconTable />,
            content: <BuildOrderTable />
          },
          {
            value: 'calendar',
            label: t`Calendar View`,
            icon: <IconCalendar />,
            content: <BuildOrderCalendar />
          },
          {
            value: 'parametric',
            label: t`Parametric View`,
            icon: <IconListDetails />,
            content: <BuildOrderParametricTable />
          }
        ]
      })
    ];
  }, [user, buildOrderView]);

  if (!user.isLoggedIn() || !user.hasViewRole(UserRoles.build)) {
    return <PermissionDenied />;
  }

  return (
    <Stack>
      <PageDetail title={t`Manufacturing`} actions={[]} />
      <PanelGroup
        pageKey='build-index'
        panels={panels}
        pluginPanelWithoutId
        pluginPanelKey={PluginPanelKey.manufacturing}
      />
    </Stack>
  );
}
