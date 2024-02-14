import { t } from '@lingui/macro';
import {
  ActionIcon,
  Indicator,
  IndicatorProps,
  Menu,
  Tooltip
} from '@mantine/core';
import {
  IconCopy,
  IconEdit,
  IconLink,
  IconQrcode,
  IconTrash,
  IconUnlink
} from '@tabler/icons-react';
import { ReactNode, useMemo } from 'react';

import { notYetImplemented } from '../../functions/notifications';

export type ActionDropdownItem = {
  icon: ReactNode;
  name: string;
  tooltip?: string;
  disabled?: boolean;
  onClick?: () => void;
  indicator?: Omit<IndicatorProps, 'children'>;
};

/**
 * A simple Menu component which renders a set of actions.
 *
 * If no "active" actions are provided, the menu will not be rendered
 */
export function ActionDropdown({
  icon,
  tooltip,
  actions
}: {
  icon: ReactNode;
  tooltip?: string;
  actions: ActionDropdownItem[];
}) {
  const hasActions = useMemo(() => {
    return actions.some((action) => !action.disabled);
  }, [actions]);
  const indicatorProps = useMemo(() => {
    return actions.find((action) => action.indicator);
  }, [actions]);

  return hasActions ? (
    <Menu position="bottom-end">
      <Indicator disabled={!indicatorProps} {...indicatorProps?.indicator}>
        <Menu.Target>
          <Tooltip label={tooltip} hidden={!tooltip}>
            <ActionIcon size="lg" radius="sm" variant="outline">
              {icon}
            </ActionIcon>
          </Tooltip>
        </Menu.Target>
      </Indicator>
      <Menu.Dropdown>
        {actions.map((action) =>
          action.disabled ? null : (
            <Indicator
              disabled={!action.indicator}
              {...action.indicator}
              key={action.name}
            >
              <Tooltip label={action.tooltip}>
                <Menu.Item
                  icon={action.icon}
                  onClick={() => {
                    if (action.onClick != undefined) {
                      action.onClick();
                    } else {
                      notYetImplemented();
                    }
                  }}
                  disabled={action.disabled}
                >
                  {action.name}
                </Menu.Item>
              </Tooltip>
            </Indicator>
          )
        )}
      </Menu.Dropdown>
    </Menu>
  ) : null;
}

// Dropdown menu for barcode actions
export function BarcodeActionDropdown({
  actions
}: {
  actions: ActionDropdownItem[];
}) {
  return (
    <ActionDropdown
      key="barcode-actions"
      tooltip={t`Barcode Actions`}
      icon={<IconQrcode />}
      actions={actions}
    />
  );
}

// Common action button for viewing a barcode
export function ViewBarcodeAction({
  disabled = false,
  onClick
}: {
  disabled?: boolean;
  onClick?: () => void;
}): ActionDropdownItem {
  return {
    icon: <IconQrcode />,
    name: t`View`,
    tooltip: t`View barcode`,
    onClick: onClick,
    disabled: disabled
  };
}

// Common action button for linking a custom barcode
export function LinkBarcodeAction({
  disabled = false,
  onClick
}: {
  disabled?: boolean;
  onClick?: () => void;
}): ActionDropdownItem {
  return {
    icon: <IconLink />,
    name: t`Link Barcode`,
    tooltip: t`Link custom barcode`,
    onClick: onClick,
    disabled: disabled
  };
}

// Common action button for un-linking a custom barcode
export function UnlinkBarcodeAction({
  disabled = false,
  onClick
}: {
  disabled?: boolean;
  onClick?: () => void;
}): ActionDropdownItem {
  return {
    icon: <IconUnlink />,
    name: t`Unlink Barcode`,
    tooltip: t`Unlink custom barcode`,
    onClick: onClick,
    disabled: disabled
  };
}

// Common action button for editing an item
export function EditItemAction({
  disabled = false,
  tooltip,
  onClick
}: {
  disabled?: boolean;
  tooltip?: string;
  onClick?: () => void;
}): ActionDropdownItem {
  return {
    icon: <IconEdit color="blue" />,
    name: t`Edit`,
    tooltip: tooltip ?? `Edit item`,
    onClick: onClick,
    disabled: disabled
  };
}

// Common action button for deleting an item
export function DeleteItemAction({
  disabled = false,
  tooltip,
  onClick
}: {
  disabled?: boolean;
  tooltip?: string;
  onClick?: () => void;
}): ActionDropdownItem {
  return {
    icon: <IconTrash color="red" />,
    name: t`Delete`,
    tooltip: tooltip ?? t`Delete item`,
    onClick: onClick,
    disabled: disabled
  };
}

// Common action button for duplicating an item
export function DuplicateItemAction({
  disabled = false,
  tooltip,
  onClick
}: {
  disabled?: boolean;
  tooltip?: string;
  onClick?: () => void;
}): ActionDropdownItem {
  return {
    icon: <IconCopy color="green" />,
    name: t`Duplicate`,
    tooltip: tooltip ?? t`Duplicate item`,
    onClick: onClick,
    disabled: disabled
  };
}
