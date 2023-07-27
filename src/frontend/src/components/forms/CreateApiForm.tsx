import { useMemo } from 'react';

import { ApiForm, ApiFormProps } from './ApiForm';

/**
 * A modal form for creating a new database object via the API
 */
export function CreateApiForm(props: ApiFormProps) {
  const createProps: ApiFormProps = useMemo(() => {
    return {
      ...props,
      method: 'POST',
      fetchInitialData: false
    };
  }, [props]);

  return <ApiForm {...createProps} />;
}
