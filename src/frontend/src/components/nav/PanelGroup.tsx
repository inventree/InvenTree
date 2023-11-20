import {
  ActionIcon,
  Divider,
  Paper,
  Stack,
  Tabs,
  Tooltip
} from '@mantine/core';
import { useLocalStorage } from '@mantine/hooks';
import {
  IconLayoutSidebarLeftCollapse,
  IconLayoutSidebarRightCollapse
} from '@tabler/icons-react';
import { ReactNode } from 'react';
import { useEffect, useState } from 'react';

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

/**
 *
 * @param panels : PanelDefinition[] - The list of panels to display
 * @param activePanel : string - The name of the currently active panel (defaults to the first panel)
 * @param setActivePanel : (panel: string) => void - Function to set the active panel
 * @param onPanelChange : (panel: string) => void - Callback when the active panel changes
 * @param collabsible : boolean - If true, the panel group can be collapsed (defaults to true)
 * @returns
 */
export function PanelGroup({
  pageKey,
  panels,
  selectedPanel,
  onPanelChange,
  collabsible = true
}: {
  pageKey: string;
  panels: PanelType[];
  selectedPanel?: string;
  onPanelChange?: (panel: string) => void;
  collabsible?: boolean;
}): ReactNode {
  const [activePanel, setActivePanel] = useLocalStorage<string>({
    key: `panel-group-active-panel-${pageKey}`,
    defaultValue: selectedPanel || panels.length > 0 ? panels[0].name : ''
  });

  // Update the active panel when the selected panel changes
  // If the selected panel is not available, default to the first available panel
  useEffect(() => {
    let activePanelNames = panels
      .filter((panel) => !panel.hidden && !panel.disabled)
      .map((panel) => panel.name);

    if (!activePanelNames.includes(activePanel)) {
      setActivePanel(activePanelNames.length > 0 ? activePanelNames[0] : '');
    }
  }, [panels]);

  // Callback when the active panel changes
  function handlePanelChange(panel: string) {
    setActivePanel(panel);

    // Optionally call external callback hook
    if (onPanelChange) {
      onPanelChange(panel);
    }
  }

  const [expanded, setExpanded] = useState<boolean>(true);

  return (
    <Paper p="sm" radius="xs" shadow="xs">
      <Tabs
        value={activePanel}
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
          {collabsible && (
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
