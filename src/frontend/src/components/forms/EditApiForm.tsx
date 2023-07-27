import { useMemo } from 'react';

import { ApiForm, ApiFormProps } from './ApiForm';

/**
 * A modal form for editing a single database object via the API.
 */
export function EditApiForm(props: ApiFormProps) {
  const editProps: ApiFormProps = useMemo(() => {
    return {
      ...props,
      method: 'PUT',
      fetchInitialData: true,
      submitText: props.submitText ? props.submitText : 'Save'
    };
  }, [props]);

  return <ApiForm {...editProps} />;
}
