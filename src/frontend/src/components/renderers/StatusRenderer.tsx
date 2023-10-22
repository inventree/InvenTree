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

const stockCodes: CodeListInterface = {};

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
