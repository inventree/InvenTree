/** Various debugging helper functions for development */

import { useEffect, useRef } from 'react';

/**
 * A custom hook that logs the previous and current props of a component whenever it updates.
 */
export function useWhyDidYouUpdate(name: string, props: any) {
  const previousProps = useRef({});

  useEffect(() => {
    if (previousProps.current) {
      const allKeys = Object.keys({ ...previousProps.current, ...props });
      const changedProps: any = {};

      allKeys.forEach((key) => {
        if ((previousProps as any).current[key] !== props[key]) {
          (changedProps as any)[key] = {
            from: (previousProps as any).current[key],
            to: props[key]
          };
        }
      });

      if (Object.keys(changedProps).length > 0) {
        console.log(`[${name}] Changed props:`, changedProps);
      }
    }

    previousProps.current = props;
  });
}
