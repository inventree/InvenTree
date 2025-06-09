import { Modal } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { useCallback } from 'react';

import type { UseModalProps, UseModalReturn } from '@lib/types/Modals';
import { StylishText } from '../components/items/StylishText';

export function useModal(props: UseModalProps): UseModalReturn {
  const onOpen = useCallback(() => {
    props.onOpen?.();
  }, [props.onOpen]);

  const onClose = useCallback(() => {
    props.onClose?.();
  }, [props.onClose]);

  const [opened, { open, close, toggle }] = useDisclosure(false, {
    onOpen,
    onClose
  });

  return {
    open,
    close,
    toggle,
    modal: (
      <Modal
        opened={opened}
        onClose={close}
        closeOnClickOutside={props.closeOnClickOutside}
        size={props.size ?? 'xl'}
        title={<StylishText size='xl'>{props.title}</StylishText>}
      >
        {props.children}
      </Modal>
    )
  };
}
