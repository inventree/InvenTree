import { t } from '@lingui/core/macro';
import { ActionIcon, Box, Group, Overlay, Paper, Tooltip } from '@mantine/core';
import { IconX } from '@tabler/icons-react';

import { Boundary } from '@lib/components/Boundary';

import type { ModelType } from '@lib/index';
import type { InvenTreeIconType } from '@lib/types/Icons';
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
  icon?: keyof InvenTreeIconType;
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
    <Paper
      withBorder
      key={item.label}
      shadow='sm'
      p='md'
      radius='lg'
      className='dashboard-widget-paper'
      style={{
        borderRadius: 20,
        cursor: 'grab',
        transition: 'box-shadow 0.2s ease, border-color 0.2s ease'
      }}
    >
      <style>{`
        .dashboard-widget-paper {
          background-color: #ffffff !important;
          border: 1.5px solid #e2e8f0 !important;
          box-shadow: 0 10px 30px -5px rgba(15, 23, 42, 0.05), 0 1px 3px rgba(0, 0, 0, 0.03) !important;
          user-select: none;
        }
        [data-mantine-color-scheme='dark'] .dashboard-widget-paper {
          background-color: #1e293b !important;
          border: 1px solid rgba(255, 255, 255, 0.08) !important;
          box-shadow: 0 10px 25px -4px rgba(0, 0, 0, 0.35) !important;
        }
        .react-grid-item.react-draggable-dragging {
          cursor: grabbing !important;
          z-index: 100 !important;
          box-shadow: 0 25px 40px -10px rgba(15, 23, 42, 0.25) !important;
          opacity: 0.92 !important;
          transition: none !important;
        }
        .react-grid-item.react-draggable-dragging * {
          cursor: grabbing !important;
          pointer-events: none !important;
        }
      `}</style>
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
