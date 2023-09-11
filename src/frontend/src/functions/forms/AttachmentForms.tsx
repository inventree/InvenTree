import { t } from '@lingui/macro';
import { Text } from '@mantine/core';

import { ApiFormFieldSet } from '../../components/forms/fields/ApiFormField';
import { openDeleteApiForm, openEditApiForm } from '../forms';

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

export function deleteAttachment({
  url,
  pk,
  callback
}: {
  url: string;
  pk: number;
  callback: () => void;
}) {
  openDeleteApiForm({
    url: url,
    pk: pk,
    name: 'attachment-edit',
    title: t`Delete Attachment`,
    successMessage: t`Attachment deleted`,
    onFormSuccess: callback,
    fields: {},
    preFormContent: (
      <Text>{t`Are you sure you want to delete this attachment?`}</Text>
    )
  });
}
