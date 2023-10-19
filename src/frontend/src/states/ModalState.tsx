import { create } from 'zustand';

interface ModalStateProps {
  loading: boolean;
  lock: () => void;
  unlock: () => void;
}

/**
 * Global state manager for modal forms.
 */
export const useModalState = create<ModalStateProps>((set) => ({
  loading: false,
  lock: () => set(() => ({ loading: true })),
  unlock: () => set(() => ({ loading: false }))
}));
