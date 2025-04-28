import {
  ActionIcon,
  Divider,
  Group,
  Loader,
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

import type { ModelType } from '@lib/enums/ModelType';
import { cancelEvent } from '@lib/functions/Events';
import { navigateToLink } from '@lib/functions/Navigation';
import { t } from '@lingui/core/macro';
import { useShallow } from 'zustand/react/shallow';
import { identifierString } from '../../functions/conversion';
import { usePluginPanels } from '../../hooks/UsePluginPanels';
import { useLocalState } from '../../states/LocalState';
import { Boundary } from '../Boundary';
import { StylishText } from '../items/StylishText';
import type { PanelGroupType, PanelType } from '../panels/Panel';
import * as classes from './PanelGroup.css';

/**
 * Set of properties which define a panel group:
 *
 * @param pageKey - Unique key for this panel group
 * @param panels - List of panels to display
 * @param model - The target model for this panel group (e.g. 'part' / 'salesorder')
 * @param id - The target ID for this panel group (set to *null* for groups which do not target a specific model instance)
 * @param instance - The target model instance for this panel group
 * @param reloadInstance - Function to reload the model instance
 * @param selectedPanel - The currently selected panel
 * @param onPanelChange - Callback when the active panel changes
 * @param collapsible - If true, the panel group can be collapsed (defaults to true)
 */
export type PanelProps = {
  pageKey: string;
  panels: PanelType[];
  groups?: PanelGroupType[];
  instance?: any;
  reloadInstance?: () => void;
  model?: ModelType | string;
  id?: number | null;
  selectedPanel?: string;
  onPanelChange?: (panel: string) => void;
  collapsible?: boolean;
  markCustomPanels?: boolean;
};

function BasePanelGroup({
  pageKey,
  panels,
  groups,
  onPanelChange,
  selectedPanel,
  reloadInstance,
  instance,
  model,
  id,
  collapsible = true,
  markCustomPanels = false
}: Readonly<PanelProps>): ReactNode {
  const localState = useLocalState();
  const location = useLocation();
  const navigate = useNavigate();

  const { panel } = useParams();

  const [expanded, setExpanded] = useState<boolean>(true);

  // Hook to load plugins for this panel
  const pluginPanelSet = usePluginPanels({
    id: id,
    model: model,
    instance: instance,
    reloadFunc: reloadInstance
  });

  // Rebuild the list of panels
  const [allPanels, groupedPanels] = useMemo(() => {
    const _grouped_pannels: PanelGroupType[] = [];
    const _panels = [...panels];
    const _allpanels: PanelType[] = [...panels];

    groups?.forEach((group) => {
      const newVal: any = { ...group, panels: [] };
      // Add panel to group and remove from main list
      group.panelIDs?.forEach((panelID) => {
        const index = _panels.findIndex((p) => p.name === panelID);
        if (index !== -1) {
          newVal.panels.push(_panels[index]);
          _panels.splice(index, 1);
        }
      });
      _grouped_pannels.push(newVal);
    });

    // Add remaining panels to group
    if (_panels.length > 0) {
      _grouped_pannels.push({
        id: 'ungrouped',
        label: '',
        panels: _panels
      });
    }

    // Add plugin panels
    const pluginPanels: any = [];
    pluginPanelSet.panels?.forEach((panel) => {
      let panelKey = panel.name;

      // Check if panel with this name already exists
      const existingPanel = panels.find((p) => p.name === panelKey);

      if (existingPanel) {
        // Create a unique key for the panel which includes the plugin slug
        panelKey = identifierString(`${panel.pluginName}-${panel.name}`);
      }

      pluginPanels.push({
        ...panel,
        name: panelKey
      });
    });

    if (pluginPanels.length > 0) {
      _grouped_pannels.push({
        id: 'plugins',
        label: markCustomPanels ? t`Plugins` : '',
        panels: pluginPanels
      });
    }

    return [_allpanels, _grouped_pannels];
  }, [groups, panels, pluginPanelSet]);

  const activePanels = useMemo(
    () => allPanels.filter((panel) => !panel.hidden && !panel.disabled),
    [allPanels]
  );

  // Callback when the active panel changes
  const handlePanelChange = useCallback(
    (targetPanel: string, event?: any) => {
      if (event && (event?.ctrlKey || event?.shiftKey)) {
        const url = `${location.pathname}/../${targetPanel}`;
        cancelEvent(event);
        navigateToLink(url, navigate, event);
      } else {
        navigate(`../${targetPanel}`);
      }

      localState.setLastUsedPanel(pageKey)(targetPanel);

      // Optionally call external callback hook
      if (targetPanel && onPanelChange) {
        onPanelChange(targetPanel);
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
          classNames={{ tab: classes.selectedPanelTab }}
        >
          <Tabs.List justify='left' aria-label={`panel-tabs-${pageKey}`}>
            {groupedPanels.map((group) => {
              const groupTabls = group.panels?.map(
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
              );

              return (
                <>
                  <strong>{group.label}</strong>
                  {groupTabls}
                </>
              );
            })}
            {collapsible && (
              <Group wrap='nowrap' gap='xs'>
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
                {pluginPanelSet.isLoading && <Loader size='xs' />}
              </Group>
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
                        <Group justify='space-between'>
                          <StylishText size='xl'>{panel.label}</StylishText>
                          {panel.controls && (
                            <Group justify='right' wrap='nowrap'>
                              {panel.controls}
                            </Group>
                          )}
                        </Group>
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
  const lastUsedPanel = useLocalState(
    useShallow((state) => {
      const panelName =
        selectedPanel || state.lastUsedPanels[pageKey] || panels[0]?.name;

      const panel = panels.findIndex(
        (p) => p.name === panelName && !p.disabled && !p.hidden
      );
      if (panel === -1) {
        return panels.find((p) => !p.disabled && !p.hidden)?.name || '';
      }

      return panelName;
    })
  );

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
