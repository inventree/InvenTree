import { t } from '@lingui/macro';
import { useId } from '@mantine/hooks';
import { useEffect, useMemo, useRef } from 'react';

import { ApiFormProps, OptionsApiForm } from '../components/forms/ApiForm';
import { useModal } from './UseModal';

export interface ApiFormModalProps extends ApiFormProps {
  title: string;
  cancelText?: string;
  cancelColor?: string;
  onClose?: () => void;
  onOpen?: () => void;
}

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
      onFormSuccess: (data) => {
        modalClose.current();
        props.onFormSuccess?.(data);
      },
      onFormError: () => {
        modalClose.current();
        props.onFormError?.();
      }
    }),
    [props]
  );

  const modal = useModal({
    title: formProps.title,
    onOpen: formProps.onOpen,
    onClose: formProps.onClose,
    size: 'xl',
    children: <OptionsApiForm props={formProps} id={id} />
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
      method: 'POST'
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
      method: 'PUT'
    }),
    [props]
  );

  return useApiFormModal(editProps);
}

/**
 * Open a modal form to delete a model instance
 */
export function useDeleteApiFormModal(props: ApiFormModalProps) {
  const deleteProps = useMemo<ApiFormModalProps>(
    () => ({
      ...props,
      method: 'DELETE',
      submitText: t`Delete`,
      submitColor: 'red',
      fields: {}
    }),
    [props]
  );

  return useApiFormModal(deleteProps);
}
