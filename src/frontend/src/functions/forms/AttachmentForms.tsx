import { t } from '@lingui/macro';

import { ApiFormFieldSet } from '../../components/forms/fields/ApiFormField';
import { openEditApiForm } from '../forms';

export function attachmentFields(editing: boolean): ApiFormFieldSet {
  let fields: ApiFormFieldSet = {
    attachment: {},
    comment: {}
  };

  if (editing) {
    delete fields['attachment'];
  }

  return fields;
}

// TODO: Function to create/upload a new attachment

export function editAttachment({
  url,
  model,
  pk,
  callback
}: {
  url: string;
  model: string;
  pk: number;
  callback?: () => void;
}) {
  let formFields = {
    ...attachmentFields(true)
  };

  formFields[model] = {
    value: pk,
    hidden: true
  };

  openEditApiForm({
    name: 'attachment-edit',
    title: t`Edit Attachment`,
    url: url,
    pk: pk,
    successMessage: t`Attachment updated`,
    fields: formFields,
    onFormSuccess: callback
  });
}
