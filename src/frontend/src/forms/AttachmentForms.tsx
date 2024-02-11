import { t } from '@lingui/macro';

import { ApiFormFieldSet } from '../components/forms/fields/ApiFormField';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import {
  openCreateApiForm,
  openDeleteApiForm,
  openEditApiForm
} from '../functions/forms';

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
  endpoint,
  model,
  pk,
  attachmentType,
  callback
}: {
  endpoint: ApiEndpoints;
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
    title: title,
    url: endpoint,
    successMessage: message,
    fields: formFields,
    onFormSuccess: callback
  });
}

/**
 * Edit an existing attachment (either a file or a link)
 */
export function editAttachment({
  endpoint,
  model,
  pk,
  attachmentType,
  callback
}: {
  endpoint: ApiEndpoints;
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
    title: title,
    url: endpoint,
    pk: pk,
    successMessage: message,
    fields: formFields,
    onFormSuccess: callback
  });
}

export function deleteAttachment({
  endpoint,
  pk,
  callback
}: {
  endpoint: ApiEndpoints;
  pk: number;
  callback: () => void;
}) {
  openDeleteApiForm({
    url: endpoint,
    pk: pk,
    title: t`Delete Attachment`,
    successMessage: t`Attachment deleted`,
    onFormSuccess: callback,
    fields: {},
    preFormWarning: t`Are you sure you want to delete this attachment?`
  });
}
