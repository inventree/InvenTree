import { create } from 'zustand';

interface ModalStateProps {
  loading: boolean;
  lock: () => void;
  unlock: () => void;
}

/**
 * Global state manager for modal forms.
 */
export const useModalState = create<ModalStateProps>((set, get) => ({
  loading: false,
  lock: () => set((state) => ({ loading: true })),
  unlock: () => set((state) => ({ loading: false }))
}));
