import { Divider, Paper, Stack, Tabs } from '@mantine/core';
import { ReactNode } from 'react';
import { useEffect, useState } from 'react';

import { StylishText } from '../items/StylishText';

/**
 * Type used to specify a single panel in a panel group
 */
export type PanelType = {
  name: string;
  label: string;
  icon?: ReactNode;
  content: ReactNode;
  hidden?: boolean;
  disabled?: boolean;
};

/**
 *
 * @param panels : PanelDefinition[] - The list of panels to display
 * @param activePanel : string - The name of the currently active panel (defaults to the first panel)
 * @param setActivePanel : (panel: string) => void - Function to set the active panel
 * @param onPanelChange : (panel: string) => void - Callback when the active panel changes
 * @returns
 */
export function PanelGroup({
  panels,
  selectedPanel,
  onPanelChange
}: {
  panels: PanelType[];
  selectedPanel?: string;
  onPanelChange?: (panel: string) => void;
}): ReactNode {
  // Default to the provided panel name, or the first panel
  const [activePanelName, setActivePanelName] = useState<string>(
    selectedPanel || panels.length > 0 ? panels[0].name : ''
  );

  // Update the active panel when the selected panel changes
  useEffect(() => {
    if (selectedPanel) {
      setActivePanelName(selectedPanel);
    }
  }, [selectedPanel]);

  // Callback when the active panel changes
  function handlePanelChange(panel: string) {
    setActivePanelName(panel);

    // Optionally call external callback hook
    if (onPanelChange) {
      onPanelChange(panel);
    }
  }

  return (
    <Paper p="sm" radius="xs" shadow="xs">
      <Tabs
        value={activePanelName}
        orientation="vertical"
        onTabChange={handlePanelChange}
        keepMounted={false}
      >
        <Tabs.List>
          {panels.map(
            (panel, idx) =>
              !panel.hidden && (
                <Tabs.Tab
                  key={`panel-tab-${panel.name}`}
                  p="xs"
                  value={panel.name}
                  icon={panel.icon}
                  hidden={panel.hidden}
                >
                  {panel.label}
                </Tabs.Tab>
              )
          )}
        </Tabs.List>
        {panels.map(
          (panel, idx) =>
            !panel.hidden && (
              <Tabs.Panel key={idx} value={panel.name} p="sm">
                <Stack spacing="md">
                  <StylishText size="lg">{panel.label}</StylishText>
                  <Divider />
                  {panel.content}
                </Stack>
              </Tabs.Panel>
            )
        )}
      </Tabs>
    </Paper>
  );
}
