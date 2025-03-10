import { useMemo } from 'react';

import { getStatusCodes } from '../components/render/StatusRenderer';
import type { ModelType } from '../enums/ModelType';
import { useGlobalStatusState } from '../states/StatusState';

/**
 * Hook to access status codes, which are enumerated by the backend.
 *
 * This hook is used to return a map of status codes for a given model type.
 * It is a memoized wrapper around getStatusCodes,
 * and returns a simplified KEY:value map of status codes.
 *
 * e.g. for the "PurchaseOrderStatus" enumeration, returns a map like:
 *
 * {
 *   PENDING: 10
 *   PLACED: 20
 *   ON_HOLD: 25,
 *   COMPLETE: 30,​
 *   CANCELLED: 40,
 *   LOST: 50,
 *   RETURNED: 60
 * }
 */
export default function useStatusCodes({
  modelType
}: {
  modelType: ModelType | string;
}) {
  const statusCodeList = useGlobalStatusState.getState().status;

  const codes = useMemo(() => {
    const statusCodes = getStatusCodes(modelType) || null;

    const codesMap: Record<any, any> = {};

    if (!statusCodes) {
      return codesMap;
    }

    Object.keys(statusCodes.values).forEach((name) => {
      codesMap[name] = statusCodes.values[name].key;
    });

    return codesMap;
  }, [modelType, statusCodeList]);

  return codes;
}
