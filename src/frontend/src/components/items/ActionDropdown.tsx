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

import { identifierString } from '../../functions/conversion';
import { InvenTreeIcon } from '../../functions/icons';
import { notYetImplemented } from '../../functions/notifications';

export type ActionDropdownItem = {
  icon: ReactNode;
  name: string;
  tooltip?: string;
  disabled?: boolean;
  hidden?: boolean;
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
  actions,
  disabled = false
}: {
  icon: ReactNode;
  tooltip: string;
  actions: ActionDropdownItem[];
  disabled?: boolean;
}) {
  const hasActions = useMemo(() => {
    return actions.some((action) => !action.hidden);
  }, [actions]);

  const indicatorProps = useMemo(() => {
    return actions.find((action) => action.indicator);
  }, [actions]);

  const menuName: string = useMemo(() => {
    return identifierString(`action-menu-${tooltip}`);
  }, [tooltip]);

  return hasActions ? (
    <Menu position="bottom-end" key={menuName}>
      <Indicator disabled={!indicatorProps} {...indicatorProps?.indicator}>
        <Menu.Target>
          <Tooltip label={tooltip} hidden={!tooltip}>
            <ActionIcon
              size="lg"
              radius="sm"
              variant="outline"
              disabled={disabled}
              aria-label={menuName}
            >
              {icon}
            </ActionIcon>
          </Tooltip>
        </Menu.Target>
      </Indicator>
      <Menu.Dropdown>
        {actions.map((action) => {
          const id: string = identifierString(`${menuName}-${action.name}`);
          return action.hidden ? null : (
            <Indicator
              disabled={!action.indicator}
              {...action.indicator}
              key={action.name}
            >
              <Tooltip label={action.tooltip} hidden={!action.tooltip}>
                <Menu.Item
                  aria-label={id}
                  leftSection={action.icon}
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
          );
        })}
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
      tooltip={t`Barcode Actions`}
      icon={<IconQrcode />}
      actions={actions}
    />
  );
}

// Common action button for viewing a barcode
export function ViewBarcodeAction({
  hidden = false,
  onClick
}: {
  hidden?: boolean;
  onClick?: () => void;
}): ActionDropdownItem {
  return {
    icon: <IconQrcode />,
    name: t`View`,
    tooltip: t`View barcode`,
    onClick: onClick,
    hidden: hidden
  };
}

// Common action button for linking a custom barcode
export function LinkBarcodeAction({
  hidden = false,
  onClick
}: {
  hidden?: boolean;
  onClick?: () => void;
}): ActionDropdownItem {
  return {
    icon: <IconLink />,
    name: t`Link Barcode`,
    tooltip: t`Link custom barcode`,
    onClick: onClick,
    hidden: hidden
  };
}

// Common action button for un-linking a custom barcode
export function UnlinkBarcodeAction({
  hidden = false,
  onClick
}: {
  hidden?: boolean;
  onClick?: () => void;
}): ActionDropdownItem {
  return {
    icon: <IconUnlink />,
    name: t`Unlink Barcode`,
    tooltip: t`Unlink custom barcode`,
    onClick: onClick,
    hidden: hidden
  };
}

// Common action button for editing an item
export function EditItemAction({
  hidden = false,
  tooltip,
  onClick
}: {
  hidden?: boolean;
  tooltip?: string;
  onClick?: () => void;
}): ActionDropdownItem {
  return {
    icon: <IconEdit color="blue" />,
    name: t`Edit`,
    tooltip: tooltip ?? `Edit item`,
    onClick: onClick,
    hidden: hidden
  };
}

// Common action button for deleting an item
export function DeleteItemAction({
  hidden = false,
  disabled = false,
  tooltip,
  onClick
}: {
  hidden?: boolean;
  disabled?: boolean;
  tooltip?: string;
  onClick?: () => void;
}): ActionDropdownItem {
  return {
    icon: <IconTrash color="red" />,
    name: t`Delete`,
    tooltip: tooltip ?? t`Delete item`,
    onClick: onClick,
    hidden: hidden,
    disabled: disabled
  };
}

export function CancelItemAction({
  hidden = false,
  tooltip,
  onClick
}: {
  hidden?: boolean;
  tooltip?: string;
  onClick?: () => void;
}): ActionDropdownItem {
  return {
    icon: <InvenTreeIcon icon="cancel" iconProps={{ color: 'red' }} />,
    name: t`Cancel`,
    tooltip: tooltip ?? t`Cancel`,
    onClick: onClick,
    hidden: hidden
  };
}

// Common action button for duplicating an item
export function DuplicateItemAction({
  hidden = false,
  tooltip,
  onClick
}: {
  hidden?: boolean;
  tooltip?: string;
  onClick?: () => void;
}): ActionDropdownItem {
  return {
    icon: <IconCopy color="green" />,
    name: t`Duplicate`,
    tooltip: tooltip ?? t`Duplicate item`,
    onClick: onClick,
    hidden: hidden
  };
}
