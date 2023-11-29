import { MantineNumberSize, Modal } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import React, { useCallback } from 'react';

import { StylishText } from '../components/items/StylishText';

export interface UseModalProps {
  title: string;
  children: React.ReactElement;
  size?: MantineNumberSize;
  onOpen?: () => void;
  onClose?: () => void;
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
        size={props.size ?? 'xl'}
        title={<StylishText size="xl">{props.title}</StylishText>}
      >
        {props.children}
      </Modal>
    )
  };
}
