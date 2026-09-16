import {} from '@mantine/core';
import type { ContextModalProps } from '@mantine/modals';
import { lazy } from 'react';
import type { NavigateFunction } from 'react-router-dom';

const ScanInputHandler = lazy(() =>
  import('../barcodes/BarcodeScanDialog').then((module) => ({
    default: module.ScanInputHandler
  }))
);

export function QrModal({
  context,
  id,
  innerProps
}: Readonly<
  ContextModalProps<{ modalBody: string; navigate: NavigateFunction }>
>) {
  function close() {
    context.closeModal(id);
  }
  function navigate() {
    context.closeModal(id);
  }

  return <ScanInputHandler navigate={innerProps.navigate} onClose={close} />;
}
