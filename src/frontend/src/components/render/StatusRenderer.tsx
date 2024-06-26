import { Badge, Center, MantineSize } from '@mantine/core';

import { colorMap } from '../../defaults/backendMappings';
import { ModelType } from '../../enums/ModelType';
import { useGlobalStatusState } from '../../states/StatusState';

interface StatusCodeInterface {
  key: string;
  label: string;
  color: string;
}

export interface StatusCodeListInterface {
  [key: string]: StatusCodeInterface;
}

interface RenderStatusLabelOptionsInterface {
  size?: MantineSize;
}

/*
 * Generic function to render a status label
 */
function renderStatusLabel(
  key: string | number,
  codes: StatusCodeListInterface,
  options: RenderStatusLabelOptionsInterface = {}
) {
  let text = null;
  let color = null;

  // Find the entry which matches the provided key
  for (let name in codes) {
    let entry = codes[name];

    if (entry.key == key) {
      text = entry.label;
      color = entry.color;
      break;
    }
  }

  if (!text) {
    console.error(`renderStatusLabel could not find match for code ${key}`);
  }

  // Fallbacks
  if (color == null) color = 'default';
  color = colorMap[color] || colorMap['default'];
  const size = options.size || 'xs';

  if (!text) {
    text = key;
  }

  return (
    <Badge color={color} variant="filled" size={size}>
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
  status: string | number;
  type: ModelType | string;
  options?: RenderStatusLabelOptionsInterface;
}) => {
  const statusCodeList = useGlobalStatusState.getState().status;

  if (status === undefined || statusCodeList === undefined) {
    return null;
  }

  const statusCodes = statusCodeList[type];
  if (statusCodes === undefined) {
    console.warn('StatusRenderer: statusCodes is undefined');
    return null;
  }

  return renderStatusLabel(status, statusCodes, options);
};

/*
 * Render the status badge in a table
 */
export function TableStatusRenderer(
  type: ModelType
): ((record: any) => any) | undefined {
  return (record: any) =>
    record.status && (
      <Center>{StatusRenderer({ status: record.status, type: type })}</Center>
    );
}
