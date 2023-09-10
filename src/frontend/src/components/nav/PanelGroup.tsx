import { Tabs } from '@mantine/core';
import { ReactNode } from 'react';
import { useState } from 'react';

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
  defaultPanel,
  onPanelChange
}: {
  panels: PanelType[];
  defaultPanel?: string;
  onPanelChange?: (panel: string) => void;
}): ReactNode {
  // Default to the provided panel name, or the first panel
  const [activePanelName, setActivePanelName] = useState<string>(
    defaultPanel || panels[0].name
  );

  // Callback when the active panel changes
  function handlePanelChange(panel: string) {
    setActivePanelName(panel);

    // Optionally call external callback hook
    if (onPanelChange) {
      onPanelChange(panel);
    }
  }

  return (
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
            <Tabs.Panel key={idx} value={panel.name}>
              {panel.content}
            </Tabs.Panel>
          )
      )}
    </Tabs>
  );
}
