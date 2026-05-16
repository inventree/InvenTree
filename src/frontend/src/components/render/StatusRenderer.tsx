import { Badge, Center, type MantineSize } from '@mantine/core';

import type { ModelType } from '@lib/enums/ModelType';
import { resolveItem } from '@lib/functions/Conversion';
import { statusColorMap } from '../../defaults/backendMappings';
import { useGlobalStatusState } from '../../states/GlobalStatusState';

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
  options: RenderStatusLabelOptionsInterface = {},
  fallback_key: string | number | null = null
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

  if (!text && fallback_key !== null) {
    // Handle fallback key (if provided)
    for (const name in codes.values) {
      const entry: StatusCodeInterface = codes.values[name];

      if (entry?.key == fallback_key) {
        text = entry.label;
        color = entry.color;
        break;
      }
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
    console.warn('StatusRenderer: statusCodeList is undefined');
    return null;
  }

  const statusCodes = statusCodeList[type];

  if (statusCodes === undefined) {
    console.warn(
      `StatusRenderer: statusCodes is undefined for model '${type}'`
    );
    return null;
  }

  return statusCodes;
}

/**
 * Return a list of status codes select options for a given model type
 * returns an array of objects with keys "value" and "display_name"
 *
 */
export function getStatusCodeOptions(type: ModelType | string): any[] {
  const statusCodes = getStatusCodes(type);

  if (!statusCodes) {
    return [];
  }

  return Object.values(statusCodes?.values ?? []).map((entry) => {
    return {
      value: entry.key,
      display_name: entry.label
    };
  });
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
 * Return the human-readable label for a status code
 */
export function getStatusCodeLabel(
  type: ModelType | string,
  key: string | number
): string | null {
  const statusCodes = getStatusCodes(type);

  if (!statusCodes) {
    return null;
  }

  for (const name in statusCodes.values) {
    const entry: StatusCodeInterface = statusCodes.values[name];

    if (entry.key == key) {
      return entry.label;
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
  options,
  fallbackStatus
}: {
  status: string | number;
  type: ModelType | string;
  options?: RenderStatusLabelOptionsInterface;
  fallbackStatus?: string | number | null;
}) => {
  const statusCodes = getStatusCodes(type);

  if (options?.hidden) {
    return null;
  }

  if (statusCodes === undefined || statusCodes === null) {
    console.warn(
      `StatusRenderer: statusCodes is undefined for model '${type}'`
    );
    return null;
  }

  return renderStatusLabel(status, statusCodes, options, fallbackStatus);
};

/*
 * Render the status badge in a table
 */
export function TableStatusRenderer(
  type: ModelType,
  accessor?: string
): ((record: any) => any) | undefined {
  return (record: any) => {
    const status =
      resolveItem(record, accessor ?? 'status') ??
      resolveItem(record, 'status_custom_key') ??
      resolveItem(record, 'status');

    return (
      status && (
        <Center>{StatusRenderer({ status: status, type: type })}</Center>
      )
    );
  };
}
