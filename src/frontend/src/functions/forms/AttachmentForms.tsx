import { t } from '@lingui/macro';
import { Text } from '@mantine/core';

import { ApiFormFieldSet } from '../../components/forms/fields/ApiFormField';
import { ApiPaths } from '../../states/ApiState';
import {
  openCreateApiForm,
  openDeleteApiForm,
  openEditApiForm
} from '../forms';

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

/**
 * Add a new attachment (either a file or a link)
 */
export function addAttachment({
  url,
  model,
  pk,
  attachmentType,
  callback
}: {
  url: ApiPaths;
  model: string;
  pk: number;
  attachmentType: 'file' | 'link';
  callback?: () => void;
}) {
  let formFields: ApiFormFieldSet = {
    attachment: {},
    link: {},
    comment: {}
  };

  if (attachmentType === 'link') {
    delete formFields['attachment'];
  } else {
    delete formFields['link'];
  }

  formFields[model] = {
    value: pk,
    hidden: true
  };

  let title = attachmentType === 'file' ? t`Add File` : t`Add Link`;
  let message = attachmentType === 'file' ? t`File added` : t`Link added`;

  openCreateApiForm({
    name: 'attachment-add',
    title: title,
    url: url,
    successMessage: message,
    fields: formFields,
    onFormSuccess: callback
  });
}

/**
 * Edit an existing attachment (either a file or a link)
 */
export function editAttachment({
  url,
  model,
  pk,
  attachmentType,
  callback
}: {
  url: ApiPaths;
  model: string;
  pk: number;
  attachmentType: 'file' | 'link';
  callback?: () => void;
}) {
  let formFields: ApiFormFieldSet = {
    link: {},
    comment: {}
  };

  if (attachmentType === 'file') {
    delete formFields['link'];
  }

  formFields[model] = {
    value: pk,
    hidden: true
  };

  let title = attachmentType === 'file' ? t`Edit File` : t`Edit Link`;
  let message = attachmentType === 'file' ? t`File updated` : t`Link updated`;

  openEditApiForm({
    name: 'attachment-edit',
    title: title,
    url: url,
    pk: pk,
    successMessage: message,
    fields: formFields,
    onFormSuccess: callback
  });
}

export function deleteAttachment({
  url,
  pk,
  callback
}: {
  url: ApiPaths;
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
