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

  const isClickable = !editing && (
    !!item.modelType ||
    item.label.startsWith('sub-') ||
    item.label.startsWith('act-') ||
    item.label.startsWith('ovr-') ||
    item.label.startsWith('asn-') ||
    item.label === 'low-stk' ||
    item.label === 'hgh-stk' ||
    item.label === 'bld-req' ||
    item.label === 'invalid-bom' ||
    item.label === 'latest-parts'
  );

  const isLowLevel = item.label !== 'dash-stats' && isClickable;

  return (
    <Paper
      withBorder
      key={item.label}
      shadow='sm'
      p={item.minHeight === 1 ? 'xs' : (item.label === 'dash-stats' ? 'sm' : 'md')}
      radius='lg'
      className={`dashboard-widget-paper ${isLowLevel ? 'low-level-widget' : (isClickable ? 'dashboard-widget-clickable' : '')}`}
      style={{
        borderRadius: item.minHeight === 1 ? 16 : 20,
        cursor: editing ? 'grab' : (isClickable ? 'pointer' : undefined),
        transition: 'box-shadow 0.3s ease, border-color 0.3s ease'
      }}
    >
      <style>{`
        .dashboard-widget-paper {
          background-color: #ffffff !important;
          border: 1.5px solid #e2e8f0 !important;
          box-shadow: 0 10px 30px -5px rgba(15, 23, 42, 0.05), 0 1px 3px rgba(0, 0, 0, 0.03) !important;
        }
        [data-mantine-color-scheme='dark'] .dashboard-widget-paper {
          background-color: #1e293b !important;
          border: 1px solid rgba(255, 255, 255, 0.08) !important;
          box-shadow: 0 10px 25px -4px rgba(0, 0, 0, 0.35) !important;
        }

        /* LOW-LEVEL WIDGETS: Fluid Background Fill matching Ref Images 1 & 2 */
        .low-level-widget {
          overflow: hidden !important;
          cursor: pointer !important;
          transition: border-color 0.65s cubic-bezier(0.32, 0, 0.2, 1),
                      box-shadow 0.65s cubic-bezier(0.32, 0, 0.2, 1) !important;
          z-index: 1;
        }

        /* Expanding wave background fill from corner */
        .low-level-widget::before {
          content: '';
          position: absolute;
          inset: 0;
          background: radial-gradient(circle at 88% 22%, #034b6e 0%, #062b3d 48%, #031b27 100%);
          opacity: 0;
          clip-path: circle(0% at 88% 22%);
          transition: clip-path 0.95s cubic-bezier(0.32, 0, 0.2, 1),
                      opacity 0.65s ease !important;
          z-index: 0;
          pointer-events: none;
        }

        [data-mantine-color-scheme='dark'] .low-level-widget::before {
          background: radial-gradient(circle at 88% 22%, #0284c7 0%, #075985 50%, #0a2d45 100%);
        }

        .widget-inner-content {
          transition: transform 0.65s cubic-bezier(0.32, 0, 0.2, 1);
        }

        .low-level-widget:hover {
          border-color: rgba(56, 189, 248, 0.5) !important;
          box-shadow: 0 14px 30px -4px rgba(3, 27, 41, 0.28) !important;
        }

        .low-level-widget:hover .widget-inner-content {
          transform: translateY(-2px);
        }

        [data-mantine-color-scheme='dark'] .low-level-widget:hover {
          border-color: rgba(56, 189, 248, 0.65) !important;
          box-shadow: 0 14px 30px -4px rgba(0, 0, 0, 0.5) !important;
        }

        /* When hovered: the card gets filled with the bg color */
        .low-level-widget:hover::before {
          opacity: 1 !important;
          clip-path: circle(145% at 88% 22%) !important;
        }

        /* Smooth bi-directional transitions for text, numbers, and icons */
        .low-level-widget .mantine-Text-root,
        .low-level-widget .mantine-RollingNumber-root,
        .low-level-widget .mantine-RollingNumber-root span:not([class*="copyValue"]) {
          transition: color 0.65s ease, -webkit-text-fill-color 0.65s ease !important;
        }

        .low-level-widget .tabler-icon {
          transition: stroke 0.65s ease, filter 0.65s ease !important;
        }

        .low-level-widget .widget-icon-wrapper {
          transition: background 0.65s ease,
                      border-color 0.65s ease,
                      transform 0.65s cubic-bezier(0.32, 0, 0.2, 1) !important;
        }

        /* Mantine RollingNumber copyValue span is for clipboard/accessibility only; it MUST remain transparent */
        .low-level-widget span[class*="copyValue"],
        .low-level-widget:hover span[class*="copyValue"] {
          color: transparent !important;
          -webkit-text-fill-color: transparent !important;
          background: transparent !important;
        }

        /* Text, numbers, and icons turn crisp white and luminous cyan on hover */
        .low-level-widget:hover .mantine-Text-root,
        .low-level-widget:hover .mantine-RollingNumber-root,
        .low-level-widget:hover .mantine-RollingNumber-root span:not([class*="copyValue"]) {
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
        }

        .low-level-widget:hover .tabler-icon {
          stroke: #38bdf8 !important;
          filter: drop-shadow(0 0 6px rgba(56, 189, 248, 0.5));
        }

        .low-level-widget:hover .widget-icon-wrapper {
          background: rgba(56, 189, 248, 0.22) !important;
          border-color: rgba(56, 189, 248, 0.4) !important;
          transform: scale(1.06);
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
          className='widget-inner-content'
          style={{
            position: 'relative',
            zIndex: 1,
            width: '100%',
            height: '100%',
            padding: '0px',
            margin: '0px',
            overflowY:
              item.minHeight === 1 || item.label === 'dash-stats'
                ? 'visible'
                : 'hidden'
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
