import { t } from '@lingui/macro';
import { useMemo } from 'react';

import { ApiForm, ApiFormProps } from './ApiForm';

/**
 * A modal form for deleting a single database object via the API.
 */
export function DeleteApiForm(props: ApiFormProps) {
  const deleteProps: ApiFormProps = useMemo(() => {
    return {
      ...props,
      method: 'DELETE',
      fetchInitialData: false,
      submitText: props.submitText ? props.submitText : t`Delete`,
      submitColor: 'red'
    };
  }, [props]);

  return <ApiForm {...deleteProps} />;
}
