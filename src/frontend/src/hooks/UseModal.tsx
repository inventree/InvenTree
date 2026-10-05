import { Modal } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { useCallback } from 'react';

import { StylishText } from '@lib/components/StylishText';
import type { UseModalProps, UseModalReturn } from '@lib/types/Modals';
import { useUserSettingsState } from '../states/SettingsStates';

export function useModal(props: UseModalProps): UseModalReturn {
  const onOpen = useCallback(() => {
    props.onOpen?.();
  }, [props.onOpen]);

  const userSettings = useUserSettingsState();

  const onClose = useCallback(() => {
    props.onClose?.();
  }, [props.onClose]);

  const [opened, { open, close, toggle }] = useDisclosure(false, {
    onOpen,
    onClose
  });

  const isWide =
    props.size === '95%' || props.size === '90%' || props.size === '85%';

  return {
    open,
    close,
    toggle,
    modal: (
      <Modal
        key={props.id}
        opened={opened}
        closeOnEscape={userSettings.isSet('FORMS_CLOSE_USING_ESCAPE')}
        onClose={close}
        closeOnClickOutside={props.closeOnClickOutside}
        size={isWide ? '95%' : (props.size ?? 'xl')}
        yOffset={isWide ? '2.5vh' : undefined}
        xOffset={isWide ? '2.5vw' : undefined}
        centered
        className={isWide ? 'modal-95' : undefined}
        styles={
          isWide
            ? {
                root: {
                  '--modal-size': '95vw',
                  '--modal-y-offset': '2.5vh',
                  '--modal-x-offset': '2.5vw',
                  '--modal-inner-y-offset': '2.5vh',
                  '--modal-inner-x-offset': '2.5vw'
                } as any,
                inner: {
                  padding: '2.5vh 2.5vw',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '100vh',
                  maxHeight: '100vh',
                  width: '100vw',
                  maxWidth: '100vw'
                },
                content: {
                  width: '95vw',
                  minWidth: '95vw',
                  maxWidth: '95vw',
                  height: '95vh',
                  minHeight: '95vh',
                  maxHeight: '95vh',
                  display: 'flex',
                  flexDirection: 'column',
                  overflow: 'hidden',
                  borderRadius: '8px'
                },
                header: {
                  padding: '8px 16px',
                  minHeight: '40px',
                  flexShrink: 0,
                  borderBottom: '1px solid var(--mantine-color-default-border)'
                },
                body: {
                  flex: '1 1 0%',
                  minHeight: 0,
                  display: 'flex',
                  flexDirection: 'column',
                  overflow: 'hidden',
                  padding: '8px 16px 10px 16px'
                }
              }
            : undefined
        }
        title={<StylishText size='lg'>{props.title}</StylishText>}
      >
        {props.children}
      </Modal>
    )
  };
}
