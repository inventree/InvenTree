import { t } from '@lingui/macro';
import {
  IconArrowRight,
  IconCircleX,
  IconCopy,
  IconEdit,
  IconTrash
} from '@tabler/icons-react';
import { getDetailUrl, navigateToLink } from '../functions/navigation';
import type { RowAction, RowViewProps } from './RowAction';

// Component for viewing a row in a table
export function RowViewAction(props: RowViewProps): RowAction {
  return {
    ...props,
    color: undefined,
    icon: <IconArrowRight />,
    onClick: (event: any) => {
      const url = getDetailUrl(props.modelType, props.modelId);
      navigateToLink(url, props.navigate, event);
    }
  };
}

// Component for duplicating a row in a table
export function RowDuplicateAction(props: RowAction): RowAction {
  return {
    ...props,
    title: t`Duplicate`,
    color: 'green',
    icon: <IconCopy />
  };
}

// Component for editing a row in a table
export function RowEditAction(props: RowAction): RowAction {
  return {
    ...props,
    title: t`Edit`,
    color: 'blue',
    icon: <IconEdit />
  };
}

// Component for deleting a row in a table
export function RowDeleteAction(props: RowAction): RowAction {
  return {
    ...props,
    title: t`Delete`,
    color: 'red',
    icon: <IconTrash />
  };
}

// Component for cancelling a row in a table
export function RowCancelAction(props: RowAction): RowAction {
  return {
    ...props,
    title: t`Cancel`,
    color: 'red',
    icon: <IconCircleX />
  };
}
