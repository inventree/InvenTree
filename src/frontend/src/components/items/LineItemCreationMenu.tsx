import { IconFileUpload, IconPlus } from '@tabler/icons-react';

import { ActionDropdown } from './ActionDropdown';

/**
 * A split "add" button which allows either direct creation of a single line item,
 * or bulk creation via a data import session.
 */
export function LineItemCreationMenu({
  tooltip,
  addLabel,
  importLabel,
  hidden = false,
  enableImport = true,
  onAdd,
  onImport
}: Readonly<{
  tooltip: string;
  addLabel: string;
  importLabel: string;
  hidden?: boolean;
  enableImport?: boolean;
  onAdd: () => void;
  onImport: () => void;
}>) {
  return (
    <ActionDropdown
      key='add-line-item-actions'
      tooltip={tooltip}
      position='bottom-start'
      icon={<IconPlus />}
      hidden={hidden}
      actions={[
        {
          name: addLabel,
          icon: <IconPlus />,
          onClick: onAdd
        },
        {
          name: importLabel,
          icon: <IconFileUpload />,
          hidden: !enableImport,
          onClick: onImport
        }
      ]}
    />
  );
}
