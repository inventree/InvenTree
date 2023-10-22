import { t } from '@lingui/macro';
import { Badge, MantineSize } from '@mantine/core';

import { ModelType } from '../render/ModelType';

interface CodeInterface {
  key: number;
  value: string;
  label: string;
  help_text: string;
}

interface CodeListInterface {
  [key: string]: CodeInterface;
}

const stockCodes: CodeListInterface = {
  pending: {
    key: 10,
    value: t`Pending`,
    label: 'gray',
    help_text: t`Order is pending (not yet placed)`
  },
  pending_placing: {
    key: 15,
    value: t`Pending placing`,
    label: 'gray',
    help_text: t`Order is pending an action for being placed`
  },
  pending_approval: {
    key: 16,
    value: t`Pending approval`,
    label: 'gray',
    help_text: t`Order is pending approval`
  },
  placed: {
    key: 20,
    value: t`Placed`,
    label: 'blue',
    help_text: t`Order has been placed with supplier`
  },
  complete: {
    key: 30,
    value: t`Complete`,
    label: 'green',
    help_text: t`Order has been completed`
  },
  cancelled: {
    key: 40,
    value: t`Cancelled`,
    label: 'red',
    help_text: t`Order was cancelled`
  },
  lost: {
    key: 50,
    value: t`Lost`,
    label: 'orange',
    help_text: t`Order was lost`
  },
  returned: {
    key: 60,
    value: t`Returned`,
    label: 'orange',
    help_text: t`Order was returned`
  }
};

interface renderStatusLabelOptionsInterface {
  size?: MantineSize;
}

/*
 * Generic function to render a status label
 */
function renderStatusLabel(
  key: number,
  codes: CodeListInterface,
  options: renderStatusLabelOptionsInterface = {}
) {
  let text = null;
  let label = null;

  // Find the entry which matches the provided key
  for (let name in codes) {
    let entry = codes[name];

    if (entry.key == key) {
      text = entry.value;
      label = entry.label;
      break;
    }
  }

  if (!text) {
    console.error(`renderStatusLabel could not find match for code ${key}`);
  }

  // Fallbacks
  label = label || 'dark';
  const size = options.size || 'xs';

  if (!text) {
    text = key;
  }

  return (
    <Badge color={label} variant="filled" size={size}>
      {text}
    </Badge>
  );
}
/*
 * Render the status for a object.
 * Uses the values specified in "status_codes.py"
 */
export const StatusRenderer = ({
  status,
  type,
  options
}: {
  status: number;
  type: ModelType;
  options?: renderStatusLabelOptionsInterface;
}) => {
  // TODO: use type to determine which codes to use
  return renderStatusLabel(status, stockCodes, options);
};
