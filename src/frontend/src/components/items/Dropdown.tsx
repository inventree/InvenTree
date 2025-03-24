import { t } from '@lingui/macro';
import {} from '@mantine/core';
import { modals } from '@mantine/modals';
import {
  IconCopy,
  IconEdit,
  IconLink,
  IconQrcode,
  IconTrash,
  IconUnlink
} from '@tabler/icons-react';
import type { ReactNode } from 'react';

import {
  ActionDropdown,
  type ActionDropdownItem,
  InvenTreeIcon
} from '@lib/components';
import { StylishText } from '@lib/components';
import type { ModelType } from '@lib/index';
import { InvenTreeQRCode, QRCodeLink, QRCodeUnlink } from '../barcodes/QRCode';

// Dropdown menu for barcode actions
export function BarcodeActionDropdown({
  model,
  pk,
  hash = null,
  actions = [],
  perm: permission = true
}: Readonly<{
  model: ModelType;
  pk: number;
  hash?: boolean | null;
  actions?: ActionDropdownItem[];
  perm?: boolean;
}>) {
  const hidden = hash === null;
  const prop = { model, pk, hash };
  return (
    <ActionDropdown
      tooltip={t`Barcode Actions`}
      icon={<IconQrcode />}
      actions={[
        GeneralBarcodeAction({
          mdl_prop: prop,
          title: t`View Barcode`,
          icon: <IconQrcode />,
          tooltip: t`View barcode`,
          ChildItem: InvenTreeQRCode
        }),
        GeneralBarcodeAction({
          hidden: hidden || hash || !permission,
          mdl_prop: prop,
          title: t`Link Barcode`,
          icon: <IconLink />,
          tooltip: t`Link a custom barcode to this item`,
          ChildItem: QRCodeLink
        }),
        GeneralBarcodeAction({
          hidden: hidden || !hash || !permission,
          mdl_prop: prop,
          title: t`Unlink Barcode`,
          icon: <IconUnlink />,
          tooltip: t`Unlink custom barcode`,
          ChildItem: QRCodeUnlink
        }),
        ...actions
      ]}
    />
  );
}

export type QrCodeType = {
  model: ModelType;
  pk: number;
  hash?: boolean | null;
};

function GeneralBarcodeAction({
  hidden = false,
  mdl_prop,
  title,
  icon,
  tooltip,
  ChildItem
}: {
  hidden?: boolean;
  mdl_prop: QrCodeType;
  title: string;
  icon: ReactNode;
  tooltip: string;
  ChildItem: any;
}): ActionDropdownItem {
  const onClick = () => {
    modals.open({
      title: <StylishText size='xl'>{title}</StylishText>,
      children: <ChildItem mdl_prop={mdl_prop} />
    });
  };

  return {
    icon: icon,
    name: title,
    tooltip: tooltip,
    onClick: onClick,
    hidden: hidden
  };
}

// Common action button for editing an item
export function EditItemAction(props: ActionDropdownItem): ActionDropdownItem {
  return {
    ...props,
    icon: <IconEdit color='blue' />,
    name: t`Edit`,
    tooltip: props.tooltip ?? t`Edit item`
  };
}

// Common action button for deleting an item
export function DeleteItemAction(
  props: ActionDropdownItem
): ActionDropdownItem {
  return {
    ...props,
    icon: <IconTrash color='red' />,
    name: t`Delete`,
    tooltip: props.tooltip ?? t`Delete item`
  };
}

export function HoldItemAction(props: ActionDropdownItem): ActionDropdownItem {
  return {
    ...props,
    icon: <InvenTreeIcon icon='hold' iconProps={{ color: 'orange' }} />,
    name: t`Hold`,
    tooltip: props.tooltip ?? t`Hold`
  };
}

export function CancelItemAction(
  props: ActionDropdownItem
): ActionDropdownItem {
  return {
    ...props,
    icon: <InvenTreeIcon icon='cancel' iconProps={{ color: 'red' }} />,
    name: t`Cancel`,
    tooltip: props.tooltip ?? t`Cancel`
  };
}

// Common action button for duplicating an item
export function DuplicateItemAction(
  props: ActionDropdownItem
): ActionDropdownItem {
  return {
    ...props,
    icon: <IconCopy color='green' />,
    name: t`Duplicate`,
    tooltip: props.tooltip ?? t`Duplicate item`
  };
}
