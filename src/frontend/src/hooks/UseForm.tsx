import { t } from '@lingui/core/macro';
import { Alert, Divider, Stack } from '@mantine/core';
import { useId } from '@mantine/hooks';
import { useEffect, useMemo, useRef } from 'react';

import type {
  ApiFormModalProps,
  BulkEditApiFormModalProps
} from '@lib/types/Forms';
import { OptionsApiForm } from '../components/forms/ApiForm';
import { useModal } from './UseModal';

/**
 * Construct and open a modal form
 */
export function useApiFormModal(props: ApiFormModalProps) {
  const id = useId();
  const modalClose = useRef(() => {});

  const formProps = useMemo<ApiFormModalProps>(
    () => ({
      ...props,
      actions: [
        ...(props.actions || []),
        {
          text: props.cancelText ?? t`Cancel`,
          color: props.cancelColor ?? 'blue',
          onClick: () => {
            modalClose.current();
          }
        }
      ],
      onFormSuccess: (data, form) => {
        if (props.checkClose?.(data, form) ?? true) {
          modalClose.current();
        }
        props.onFormSuccess?.(data, form);
      },
      onFormError: (error: any, form) => {
        props.onFormError?.(error, form);
      }
    }),
    [props]
  );

  const modal = useModal({
    title: formProps.title,
    onOpen: formProps.onOpen,
    onClose: formProps.onClose,
    closeOnClickOutside: formProps.closeOnClickOutside,
    size: props.size ?? 'xl',
    children: (
      <Stack gap={'xs'}>
        <Divider />
        <OptionsApiForm props={formProps} id={id} />
      </Stack>
    )
  });

  useEffect(() => {
    modalClose.current = modal.close;
  }, [modal.close]);

  return modal;
}

/**
 * Open a modal form to create a new model instance
 */
export function useCreateApiFormModal(props: ApiFormModalProps) {
  const createProps = useMemo<ApiFormModalProps>(
    () => ({
      ...props,
      fetchInitialData: props.fetchInitialData ?? false,
      successMessage:
        props.successMessage === null
          ? null
          : (props.successMessage ?? t`Item Created`),
      method: props.method ?? 'POST'
    }),
    [props]
  );

  return useApiFormModal(createProps);
}

/**
 * Open a modal form to edit a model instance
 */
export function useEditApiFormModal(props: ApiFormModalProps) {
  const editProps = useMemo<ApiFormModalProps>(
    () => ({
      ...props,
      fetchInitialData: props.fetchInitialData ?? true,
      successMessage:
        props.successMessage === null
          ? null
          : (props.successMessage ?? t`Item Updated`),
      method: props.method ?? 'PATCH'
    }),
    [props]
  );

  return useApiFormModal(editProps);
}

export function useBulkEditApiFormModal({
  items,
  ...props
}: BulkEditApiFormModalProps) {
  const bulkEditProps = useMemo<ApiFormModalProps>(
    () => ({
      ...props,
      method: 'PATCH',
      submitText: props.submitText ?? t`Update`,
      successMessage:
        props.successMessage === null
          ? null
          : (props.successMessage ?? t`Items Updated`),
      preFormContent: props.preFormContent ?? (
        <Alert color={'blue'}>{t`Update multiple items`}</Alert>
      ),
      fields: {
        ...props.fields,
        items: {
          hidden: true,
          field_type: 'number',
          value: items
        }
      }
    }),
    [props, items]
  );

  return useApiFormModal(bulkEditProps);
}

/**
 * Open a modal form to delete a model instance
 */
export function useDeleteApiFormModal(props: ApiFormModalProps) {
  const deleteProps = useMemo<ApiFormModalProps>(
    () => ({
      ...props,
      method: props.method ?? 'DELETE',
      submitText: t`Delete`,
      submitColor: 'red',
      successMessage:
        props.successMessage === null
          ? null
          : (props.successMessage ?? t`Item Deleted`),
      preFormContent: props.preFormContent ?? (
        <Alert
          color={'red'}
        >{t`Are you sure you want to delete this item?`}</Alert>
      ),
      fields: props.fields ?? {}
    }),
    [props]
  );

  return useApiFormModal(deleteProps);
}
