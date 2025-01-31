import { Badge, Center, type MantineSize } from '@mantine/core';

import { statusColorMap } from '../../defaults/backendMappings';
import type { ModelType } from '../../enums/ModelType';
import { resolveItem } from '../../functions/conversion';
import { useGlobalStatusState } from '../../states/StatusState';

export interface StatusCodeInterface {
  key: number;
  label: string;
  name: string;
  color: string;
}

export interface StatusCodeListInterface {
  status_class: string;
  values: {
    [key: string]: StatusCodeInterface;
  };
}

interface RenderStatusLabelOptionsInterface {
  size?: MantineSize;
  hidden?: boolean;
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
  for (const name in codes.values) {
    const entry: StatusCodeInterface = codes.values[name];

    if (entry?.key == key) {
      text = entry.label;
      color = entry.color;
      break;
    }
  }

  if (!text) {
    console.error(
      `ERR: renderStatusLabel could not find match for code ${key}`
    );
  }

  // Fallbacks
  if (color == null) color = 'default';
  color = statusColorMap[color] || statusColorMap['default'];
  const size = options.size || 'xs';

  if (!text) {
    text = key;
  }

  return (
    <Badge color={color} variant='filled' size={size}>
      {text}
    </Badge>
  );
}

export function getStatusCodes(
  type: ModelType | string
): StatusCodeListInterface | null {
  const statusCodeList = useGlobalStatusState.getState().status;

  if (statusCodeList === undefined) {
    console.log('StatusRenderer: statusCodeList is undefined');
    return null;
  }

  const statusCodes = statusCodeList[type];

  if (statusCodes === undefined) {
    console.log('StatusRenderer: statusCodes is undefined');
    return null;
  }

  return statusCodes;
}

/*
 * Return the name of a status code, based on the key
 */
export function getStatusCodeName(
  type: ModelType | string,
  key: string | number
) {
  const statusCodes = getStatusCodes(type);

  if (!statusCodes) {
    return null;
  }

  for (const name in statusCodes) {
    const entry: StatusCodeInterface = statusCodes.values[name];

    if (entry.key == key) {
      return entry.name;
    }
  }

  return null;
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
  const statusCodes = getStatusCodes(type);

  if (options?.hidden) {
    return null;
  }

  if (statusCodes === undefined || statusCodes === null) {
    console.warn('StatusRenderer: statusCodes is undefined');
    return null;
  }

  return renderStatusLabel(status, statusCodes, options);
};

/*
 * Render the status badge in a table
 */
export function TableStatusRenderer(
  type: ModelType,
  accessor?: string
): ((record: any) => any) | undefined {
  return (record: any) => {
    const status = resolveItem(record, accessor ?? 'status');

    return (
      status && (
        <Center>{StatusRenderer({ status: status, type: type })}</Center>
      )
    );
  };
}
