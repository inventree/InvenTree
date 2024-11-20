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
import {
  type ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useState
} from 'react';
import {
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useParams
} from 'react-router-dom';

import type { ModelType } from '../../enums/ModelType';
import { identifierString } from '../../functions/conversion';
import { cancelEvent } from '../../functions/events';
import { navigateToLink } from '../../functions/navigation';
import { usePluginPanels } from '../../hooks/UsePluginPanels';
import { useLocalState } from '../../states/LocalState';
import { Boundary } from '../Boundary';
import { StylishText } from '../items/StylishText';
import type { PanelType } from '../panels/Panel';

/**
 * Set of properties which define a panel group:
 *
 * @param pageKey - Unique key for this panel group
 * @param panels - List of panels to display
 * @param model - The target model for this panel group (e.g. 'part' / 'salesorder')
 * @param id - The target ID for this panel group (set to *null* for groups which do not target a specific model instance)
 * @param instance - The target model instance for this panel group
 * @param selectedPanel - The currently selected panel
 * @param onPanelChange - Callback when the active panel changes
 * @param collapsible - If true, the panel group can be collapsed (defaults to true)
 */
export type PanelProps = {
  pageKey: string;
  panels: PanelType[];
  instance?: any;
  model?: ModelType | string;
  id?: number | null;
  selectedPanel?: string;
  onPanelChange?: (panel: string) => void;
  collapsible?: boolean;
};

function BasePanelGroup({
  pageKey,
  panels,
  onPanelChange,
  selectedPanel,
  instance,
  model,
  id,
  collapsible = true
}: Readonly<PanelProps>): ReactNode {
  const localState = useLocalState();
  const location = useLocation();
  const navigate = useNavigate();

  const { panel } = useParams();

  const [expanded, setExpanded] = useState<boolean>(true);

  // Hook to load plugins for this panel
  const pluginPanels = usePluginPanels({
    model: model,
    instance: instance,
    id: id
  });

  // Rebuild the list of panels
  const allPanels = useMemo(() => {
    const _panels = [...panels];

    // Add plugin panels
    pluginPanels?.forEach((panel) => {
      let panelKey = panel.name;

      // Check if panel with this name already exists
      const existingPanel = _panels.find((p) => p.name === panelKey);

      if (existingPanel) {
        // Create a unique key for the panel which includes the plugin slug
        panelKey = identifierString(`${panel.pluginName}-${panel.name}`);
      }

      _panels.push({
        ...panel,
        name: panelKey
      });
    });

    return _panels;
  }, [panels, pluginPanels]);

  const activePanels = useMemo(
    () => allPanels.filter((panel) => !panel.hidden && !panel.disabled),
    [allPanels]
  );

  // Callback when the active panel changes
  const handlePanelChange = useCallback(
    (panel: string, event?: any) => {
      if (event && (event?.ctrlKey || event?.shiftKey)) {
        const url = `${location.pathname}/../${panel}`;
        cancelEvent(event);
        navigateToLink(url, navigate, event);
      } else {
        navigate(`../${panel}`);
      }

      localState.setLastUsedPanel(pageKey)(panel);

      // Optionally call external callback hook
      if (panel && onPanelChange) {
        onPanelChange(panel);
      }
    },
    [activePanels, navigate, location, onPanelChange]
  );

  // if the selected panel state changes update the current panel
  useEffect(() => {
    if (selectedPanel && selectedPanel !== panel) {
      handlePanelChange(selectedPanel);
    }
  }, [selectedPanel, panel]);

  // Determine the current panels selection (must be a valid panel)
  const currentPanel: string = useMemo(() => {
    if (activePanels.findIndex((p) => p.name === panel) === -1) {
      return activePanels[0]?.name ?? '';
    } else {
      return panel ?? '';
    }
  }, [activePanels, panel]);

  return (
    <Boundary label={`PanelGroup-${pageKey}`}>
      <Paper p='sm' radius='xs' shadow='xs' aria-label={`${pageKey}`}>
        <Tabs
          value={currentPanel}
          orientation='vertical'
          keepMounted={false}
          aria-label={`panel-group-${pageKey}`}
        >
          <Tabs.List justify='left' aria-label={`panel-tabs-${pageKey}`}>
            {allPanels.map(
              (panel) =>
                !panel.hidden && (
                  <Tooltip
                    label={panel.label ?? panel.name}
                    key={panel.name}
                    disabled={expanded}
                    position='right'
                  >
                    <Tabs.Tab
                      p='xs'
                      key={`panel-label-${panel.name}`}
                      value={panel.name}
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
                variant='transparent'
                size='md'
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
                  key={`panel-${panel.name}`}
                  value={panel.name}
                  aria-label={`nav-panel-${identifierString(
                    `${pageKey}-${panel.name}`
                  )}`}
                  p='sm'
                  style={{
                    overflowX: 'scroll',
                    width: '100%'
                  }}
                >
                  <Stack gap='md'>
                    {panel.showHeadline !== false && (
                      <>
                        <StylishText size='xl'>{panel.label}</StylishText>
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
      <Route path='/:panel/*' element={<BasePanelGroup {...props} />} />
    </Routes>
  );
}
