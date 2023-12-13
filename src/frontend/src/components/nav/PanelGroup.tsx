import {
  ActionIcon,
  Divider,
  Paper,
  Stack,
  Tabs,
  Tooltip
} from '@mantine/core';
import {
  IconLayoutSidebarLeftCollapse,
  IconLayoutSidebarRightCollapse
} from '@tabler/icons-react';
import { ReactNode, useCallback, useMemo } from 'react';
import { useEffect, useState } from 'react';

import { useLocalState } from '../../states/LocalState';
import { PlaceholderPanel } from '../items/Placeholder';
import { StylishText } from '../items/StylishText';

/**
 * Type used to specify a single panel in a panel group
 */
export type PanelType = {
  name: string;
  label: string;
  icon?: ReactNode;
  content?: ReactNode;
  hidden?: boolean;
  disabled?: boolean;
};

export type PanelProps = {
  pageKey: string;
  panels: PanelType[];
  selectedPanel?: string;
  onPanelChange?: (panel: string) => void;
  collapsible?: boolean;
};

export function PanelGroup({
  pageKey,
  panels,
  onPanelChange,
  selectedPanel,
  collapsible = true
}: PanelProps): ReactNode {
  const localState = useLocalState();

  const [panel, setPanel] = useState<string>(selectedPanel ?? '');

  // Keep a list of active panels (hidden and disabled panels are not active)
  const activePanels = useMemo(
    () => panels.filter((panel) => !panel.hidden && !panel.disabled),
    [panels]
  );

  // Set selected panel when component is initially loaded, or when the selected panel changes
  useEffect(() => {
    let first_panel: string = activePanels[0]?.name ?? '';
    let active_panel: string =
      useLocalState.getState().getLastUsedPanel(pageKey)() ?? '';

    let panelName = selectedPanel || active_panel || first_panel;

    if (panelName != panel) {
      setPanel(panelName);
    }

    if (panelName != active_panel) {
      useLocalState.getState().setLastUsedPanel(pageKey)(panelName);
    }
  }, [activePanels, panels, selectedPanel]);

  // Callback when the active panel changes
  const handlePanelChange = useCallback(
    (panelName: string) => {
      // Ensure that the panel name is valid
      if (!activePanels.some((panel) => panel.name == panelName)) {
        return;
      }

      setPanel(panelName);
      localState.setLastUsedPanel(pageKey)(panelName);

      if (onPanelChange) {
        onPanelChange(panelName);
      }
    },
    [onPanelChange, pageKey]
  );

  const [expanded, setExpanded] = useState<boolean>(true);

  return (
    <Paper p="sm" radius="xs" shadow="xs">
      <Tabs
        value={panel}
        orientation="vertical"
        onTabChange={handlePanelChange}
        keepMounted={false}
      >
        <Tabs.List position="left">
          {panels.map(
            (panel) =>
              !panel.hidden && (
                <Tooltip
                  label={panel.label}
                  key={panel.name}
                  disabled={expanded}
                >
                  <Tabs.Tab
                    p="xs"
                    value={panel.name}
                    icon={panel.icon}
                    hidden={panel.hidden}
                  >
                    {expanded && panel.label}
                  </Tabs.Tab>
                </Tooltip>
              )
          )}
          {collapsible && (
            <ActionIcon
              style={{
                paddingLeft: '10px'
              }}
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? (
                <IconLayoutSidebarLeftCollapse opacity={0.5} />
              ) : (
                <IconLayoutSidebarRightCollapse opacity={0.5} />
              )}
            </ActionIcon>
          )}
        </Tabs.List>
        {panels.map(
          (panel) =>
            !panel.hidden && (
              <Tabs.Panel
                key={panel.name}
                value={panel.name}
                p="sm"
                style={{
                  overflowX: 'scroll',
                  width: '100%'
                }}
              >
                <Stack spacing="md">
                  <StylishText size="xl">{panel.label}</StylishText>
                  <Divider />
                  {panel.content ?? <PlaceholderPanel />}
                </Stack>
              </Tabs.Panel>
            )
        )}
      </Tabs>
    </Paper>
  );
}
