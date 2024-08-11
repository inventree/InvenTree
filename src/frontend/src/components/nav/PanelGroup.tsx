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
import { ReactNode, useCallback, useEffect, useMemo, useState } from 'react';
import {
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useParams
} from 'react-router-dom';

import { ModelType } from '../../enums/ModelType';
import { identifierString } from '../../functions/conversion';
import { navigateToLink } from '../../functions/navigation';
import { usePluginPanels } from '../../hooks/UsePluginPanels';
import { useLocalState } from '../../states/LocalState';
import { Boundary } from '../Boundary';
import { StylishText } from '../items/StylishText';
import { PanelType } from './Panel';

/**
 * Set of properties which define a panel group:
 *
 * @param pageKey - Unique key for this panel group
 * @param panels - List of panels to display
 * @param targetModel - The target model for this panel group
 * @param targetId - The target ID for this panel group (set to *null* for groups which do not target a specific model instance)
 * @param selectedPanel - The currently selected panel
 * @param onPanelChange - Callback when the active panel changes
 * @param collapsible - If true, the panel group can be collapsed (defaults to true)
 */
export type PanelProps = {
  pageKey: string;
  panels: PanelType[];
  targetInstance?: any;
  targetModel?: ModelType | string;
  targetId?: number | null;
  selectedPanel?: string;
  onPanelChange?: (panel: string) => void;
  collapsible?: boolean;
};

function BasePanelGroup({
  pageKey,
  panels,
  onPanelChange,
  selectedPanel,
  targetInstance,
  targetModel,
  targetId,
  collapsible = true
}: Readonly<PanelProps>): ReactNode {
  const location = useLocation();
  const navigate = useNavigate();
  const { panel } = useParams();

  // Hook to load plugins for this panel
  const pluginPanels = usePluginPanels({
    targetModel: targetModel,
    targetId: targetId
  });

  const allPanels = useMemo(
    () => [...panels, ...pluginPanels.panels],
    [panels, pluginPanels.panels]
  );

  const activePanels = useMemo(
    () => allPanels.filter((panel) => !panel.hidden && !panel.disabled),
    [allPanels]
  );

  const setLastUsedPanel = useLocalState((state) =>
    state.setLastUsedPanel(pageKey)
  );

  useEffect(() => {
    if (panel) {
      setLastUsedPanel(panel);
    }
    // panel is intentionally no dependency as this should only run on initial render
  }, [setLastUsedPanel]);

  // Callback when the active panel changes
  const handlePanelChange = useCallback(
    (panel: string | null, event?: any) => {
      if (activePanels.findIndex((p) => p.name === panel) === -1) {
        setLastUsedPanel('');
        return navigate('../');
      }

      if (event && (event?.ctrlKey || event?.shiftKey)) {
        const url = `${location.pathname}/../${panel}`;
        navigateToLink(url, navigate, event);
      } else {
        navigate(`../${panel}`);
      }

      // Optionally call external callback hook
      if (panel && onPanelChange) {
        onPanelChange(panel);
      }
    },
    [activePanels, setLastUsedPanel, navigate, location, onPanelChange]
  );

  // if the selected panel state changes update the current panel
  useEffect(() => {
    if (selectedPanel && selectedPanel !== panel) {
      handlePanelChange(selectedPanel);
    }
  }, [selectedPanel, panel]);

  // Update the active panel when panels changes and the active is no longer available
  useEffect(() => {
    if (activePanels.findIndex((p) => p.name === panel) === -1) {
      setLastUsedPanel('');
      return navigate('../');
    }
  }, [activePanels, panel]);

  const [expanded, setExpanded] = useState<boolean>(true);

  return (
    <Boundary label={`PanelGroup-${pageKey}`}>
      <Paper p="sm" radius="xs" shadow="xs">
        <Tabs
          value={panel}
          orientation="vertical"
          onChange={handlePanelChange}
          keepMounted={false}
        >
          <Tabs.List justify="left">
            {allPanels.map(
              (panel) =>
                !panel.hidden && (
                  <Tooltip
                    label={panel.label}
                    key={panel.name}
                    disabled={expanded}
                    position="right"
                  >
                    <Tabs.Tab
                      p="xs"
                      value={panel.name}
                      //                    icon={(<InvenTreeIcon icon={panel.name}/>)}  // Enable when implementing Icon manager everywhere
                      leftSection={panel.icon}
                      hidden={panel.hidden}
                      disabled={panel.disabled}
                      style={{ cursor: panel.disabled ? 'unset' : 'pointer' }}
                      onClick={(event: any) =>
                        handlePanelChange(panel.name, event)
                      }
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
                variant="transparent"
                size="md"
              >
                {expanded ? (
                  <IconLayoutSidebarLeftCollapse opacity={0.5} />
                ) : (
                  <IconLayoutSidebarRightCollapse opacity={0.5} />
                )}
              </ActionIcon>
            )}
          </Tabs.List>
          {allPanels.map(
            (panel) =>
              !panel.hidden && (
                <Tabs.Panel
                  key={panel.name}
                  value={panel.name}
                  aria-label={`nav-panel-${identifierString(
                    `${pageKey}-${panel.name}`
                  )}`}
                  p="sm"
                  style={{
                    overflowX: 'scroll',
                    width: '100%'
                  }}
                >
                  <Stack gap="md">
                    {panel.showHeadline !== false && (
                      <>
                        <StylishText size="xl">{panel.label}</StylishText>
                        <Divider />
                      </>
                    )}
                    <Boundary label={`PanelContent-${panel.name}`}>
                      {panel.content}
                    </Boundary>
                  </Stack>
                </Tabs.Panel>
              )
          )}
        </Tabs>
      </Paper>
    </Boundary>
  );
}

function IndexPanelComponent({
  pageKey,
  selectedPanel,
  panels
}: Readonly<PanelProps>) {
  const lastUsedPanel = useLocalState((state) => {
    const panelName =
      selectedPanel || state.lastUsedPanels[pageKey] || panels[0]?.name;

    const panel = panels.findIndex(
      (p) => p.name === panelName && !p.disabled && !p.hidden
    );
    if (panel === -1) {
      return panels.find((p) => !p.disabled && !p.hidden)?.name || '';
    }

    return panelName;
  });

  return <Navigate to={lastUsedPanel} replace />;
}

/**
 * Render a panel group. The current panel will be appended to the current url.
 * The last opened panel will be stored in local storage and opened if no panel is provided via url param
 * @param panels - The list of panels to display
 * @param onPanelChange - Callback when the active panel changes
 * @param collapsible - If true, the panel group can be collapsed (defaults to true)
 */
export function PanelGroup(props: Readonly<PanelProps>) {
  return (
    <Routes>
      <Route index element={<IndexPanelComponent {...props} />} />
      <Route path="/:panel/*" element={<BasePanelGroup {...props} />} />
    </Routes>
  );
}
