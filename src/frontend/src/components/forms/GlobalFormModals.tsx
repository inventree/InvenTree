import type { ApiFormModalProps } from '@lib/types/Forms';
import type { UseModalReturn } from '@lib/types/Modals';
import { useEffect, useMemo } from 'react';

import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import {
  type GlobalFormEntry,
  useGlobalFormState
} from '../../states/GlobalFormState';

// Delay before a closed form is removed, allowing the modal close transition to complete
const REMOVE_DELAY_MS = 500;

/**
 * Construct the form props for a global form entry,
 * ensuring that the entry is removed from the global state once the form is closed.
 */
function useGlobalFormProps(entry: GlobalFormEntry): ApiFormModalProps {
  const removeForm = useGlobalFormState((state) => state.removeForm);

  return useMemo(
    () => ({
      ...entry.props,
      modalId: entry.id,
      onClose: () => {
        entry.props.onClose?.();
        setTimeout(() => removeForm(entry.id), REMOVE_DELAY_MS);
      }
    }),
    [entry.id, entry.props]
  );
}

/**
 * Open the modal when first rendered, and close it when requested via the global state.
 */
function useGlobalFormControl(entry: GlobalFormEntry, form: UseModalReturn) {
  useEffect(() => {
    form.open();
  }, []);

  useEffect(() => {
    if (entry.closeRequested) {
      form.close();
    }
  }, [entry.closeRequested]);
}

function GlobalCreateForm({ entry }: Readonly<{ entry: GlobalFormEntry }>) {
  const form = useCreateApiFormModal(useGlobalFormProps(entry));
  useGlobalFormControl(entry, form);
  return form.modal;
}

function GlobalEditForm({ entry }: Readonly<{ entry: GlobalFormEntry }>) {
  const form = useEditApiFormModal(useGlobalFormProps(entry));
  useGlobalFormControl(entry, form);
  return form.modal;
}

function GlobalDeleteForm({ entry }: Readonly<{ entry: GlobalFormEntry }>) {
  const form = useDeleteApiFormModal(useGlobalFormProps(entry));
  useGlobalFormControl(entry, form);
  return form.modal;
}

/**
 * Render all API forms which have been opened via the global form state.
 * This allows forms to be launched from outside of a React component (e.g. by a plugin).
 */
export default function GlobalFormModals() {
  const forms = useGlobalFormState((state) => state.forms);

  return (
    <>
      {forms.map((entry) => {
        switch (entry.formType) {
          case 'create':
            return <GlobalCreateForm key={entry.id} entry={entry} />;
          case 'edit':
            return <GlobalEditForm key={entry.id} entry={entry} />;
          case 'delete':
            return <GlobalDeleteForm key={entry.id} entry={entry} />;
          default:
            return null;
        }
      })}
    </>
  );
}
