import { t } from '@lingui/macro';
import { Text } from '@mantine/core';
import { modals } from '@mantine/modals';
import { AxiosRequestConfig } from 'axios';

import { api } from '../App';
import { ApiFormProps } from '../components/forms/ApiForm';
import { invalidResponse } from './notifications';

/*
 * Construct and open a modal form
 * @param title :
 */
export function openModalApiForm({
  title,
  props
}: {
  title: string;
  props: ApiFormProps;
}) {
  // Make OPTIONS request first
  api
    .options(props.url)
    .then((response) => {
      console.log('response:', response, response.status);

      // We always expect an OPTIONS request to return 200
      if (response.status != 200) {
        invalidResponse(response.status);
        return;
      }

      modals.open({
        title: title,
        onClose: () => {
          props.onClose ? props.onClose() : null;
        },
        children: (
          <>
            <Text>Hello world</Text>
          </>
        )
      });
    })
    .catch((error) => {
      console.log('Error:', error);
      if (error.response) {
        invalidResponse(error.response.status);
      } else {
        invalidResponse(-1);
      }
    });
}

/**
 * Opens a modal form to create a new model instance
 */
export function openCreateApiForm({
  title,
  props
}: {
  title: string;
  props: ApiFormProps;
}) {
  let createProps: ApiFormProps = {
    ...props,
    method: 'POST'
  };

  openModalApiForm({
    title: title,
    props: createProps
  });
}

/**
 * Open a modal form to edit a model instance
 */
export function openEditApiForm({
  title,
  props
}: {
  title: string;
  props: ApiFormProps;
}) {
  let editProps: ApiFormProps = {
    ...props,
    method: 'PUT'
  };

  openModalApiForm({
    title: title,
    props: editProps
  });
}

/**
 * Open a modal form to delete a model instancel
 */
export function openDeleteApiForm({
  title,
  props
}: {
  title: string;
  props: ApiFormProps;
}) {
  let deleteProps: ApiFormProps = {
    ...props,
    method: 'DELETE',
    submitText: t`Delete`,
    submitColor: 'red'
  };

  openModalApiForm({
    title: title,
    props: deleteProps
  });
}
