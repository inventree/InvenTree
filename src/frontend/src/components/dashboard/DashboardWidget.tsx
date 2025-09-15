import { t } from '@lingui/core/macro';
import { ActionIcon, Box, Group, Overlay, Paper, Tooltip } from '@mantine/core';
import { IconX } from '@tabler/icons-react';

import { Boundary } from '../Boundary';

import type { ModelType } from '@lib/index';
import type { JSX } from 'react';

/**
 * Dashboard widget properties.
 *
 * @param title The title of the widget
 * @param visible A function that returns whether the widget should be visible
 * @param render A function that renders the widget
 */
export interface DashboardWidgetProps {
  label: string;
  title: string;
  description: string;
  enabled?: boolean;
  minWidth?: number;
  minHeight?: number;
  modelType?: ModelType;
  render: () => JSX.Element;
  visible?: () => boolean;
}

/**
 * Wrapper for a dashboard widget.
 */
export default function DashboardWidget({
  item,
  editing,
  removing,
  onRemove
}: Readonly<{
  item: DashboardWidgetProps;
  editing: boolean;
  removing: boolean;
  onRemove: () => void;
}>) {
  if (item.enabled == false) {
    return null;
  }

  return (
    <Paper withBorder key={item.label} shadow='sm' p='xs'>
      <Boundary label={`dashboard-widget-${item.label}`}>
        <Box
          key={`dashboard-widget-${item.label}`}
          style={{
            width: '100%',
            height: '100%',
            padding: '0px',
            margin: '0px',
            overflowY: 'hidden'
          }}
        >
          {/* Overlay to prevent mouse events when editing */}
          {editing && (
            <Box
              style={{
                position: 'absolute',
                top: 0,
                right: 0,
                bottom: 0,
                left: 0,
                backgroundColor: 'rgba(255, 255, 255, 0.5)',
                pointerEvents: 'auto'
              }}
            />
          )}
          {item.render()}
        </Box>
        {removing && (
          <Overlay color='black' opacity={0.7} zIndex={1000}>
            {removing && (
              <Group justify='right'>
                <Tooltip
                  label={t`Remove this widget from the dashboard`}
                  position='bottom'
                >
                  <ActionIcon
                    aria-label={`remove-dashboard-item-${item.label}`}
                    variant='filled'
                    color='red'
                    onClick={onRemove}
                  >
                    <IconX />
                  </ActionIcon>
                </Tooltip>
              </Group>
            )}
          </Overlay>
        )}
      </Boundary>
    </Paper>
  );
}
