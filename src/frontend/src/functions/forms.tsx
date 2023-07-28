import { t } from '@lingui/macro';
import { Text } from '@mantine/core';
import { modals } from '@mantine/modals';
import { notifications } from '@mantine/notifications';

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
  // method property *must* be supplied
  if (!props.method) {
    notifications.show({
      title: t`Invalid Form`,
      message: t`method parameter not supplied`,
      color: 'red'
    });
    return;
  }

  // Construct the url
  let url = props.url;

  if (!url.endsWith('/')) {
    url += '/';
  }

  if (props.pk && props.pk > 0) {
    url += `${props.pk}/`;
  }

  // Make OPTIONS request first
  api
    .options(url)
    .then((response) => {
      console.log('response:', response, response.status);

      // We always expect an OPTIONS request to return 200
      if (response.status != 200) {
        invalidResponse(response.status);
        return;
      }

      // Check that the correct METHOD is available ACTIONS
      let actions = (response.data?.actions ?? []) || [];

      let method = props.method?.toUpperCase() || '_';

      if (!(method in actions)) {
        notifications.show({
          title: t`Invalid Form`,
          message: t`Method ${method} not allowed`,
          color: 'red'
        });
        return;
      }

      // Extract field definitions for this endpoint
      let fields = actions[props.method?.toUpperCase() || '_'] ?? {};

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
