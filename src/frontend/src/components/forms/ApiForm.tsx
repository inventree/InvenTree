import { Modal } from '@mantine/core';
import { useForm } from '@mantine/form';

/* Definition of the ApiForm field component.
 * - The 'name' attribute *must* be provided
 * - All other attributes are optional, and may be provided by the API
 * - However, they can be overridden by the user
 */
export type ApiFormField = {
  name: string;
  label?: string;
  value?: any;
  type?: string;
  required?: boolean;
  placeholder?: string;
  help_text?: string;
  icon?: string;
  errors?: string[];
};

/**
 * An ApiForm component is a modal form which is rendered dynamically,
 * based on an API endpoint.
 * @param url : The API endpoint to fetch the form from.
 * @param fields : The fields to render in the form.
 * @param opened : Whether the form is opened or not.
 * @param onClose : A callback function to call when the form is closed.
 * @param onFormSuccess : A callback function to call when the form is submitted successfully.
 * @param onFormError : A callback function to call when the form is submitted with errors.
 */
export function ApiForm({
  url,
  title,
  fields,
  opened,
  onClose,
  onFormSuccess,
  onFormError
}: {
  url: string;
  title: string;
  fields: ApiFormField[];
  opened: boolean;
  onClose?: () => void;
  onFormSuccess?: () => void;
  onFormError?: () => void;
}) {
  // Form state
  const form = useForm({});

  return (
    <Modal opened={opened} onClose={onClose} title={title}>
      Form data goes here
    </Modal>
  );
}
