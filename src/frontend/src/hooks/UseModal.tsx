import { Modal } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import type React from 'react';
import { useCallback } from 'react';

import { StylishText } from '../components/items/StylishText';
import type { UiSizeType } from '../defaults/formatters';

export interface UseModalProps {
  title: string;
  children: React.ReactElement;
  size?: UiSizeType;
  onOpen?: () => void;
  onClose?: () => void;
  closeOnClickOutside?: boolean;
}

export function useModal(props: UseModalProps) {
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
