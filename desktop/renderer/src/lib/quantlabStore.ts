import { createStore } from 'zustand/vanilla';

export type QuantLabStoreState = {
  tabs: unknown[];
  activeTabId: string | null;
  selectedRunIds: string[];
};

export type QuantLabStoreActions = {
  setActiveTabId: (tabId: string | null) => void;
  setSelectedRunIds: (runIds: string[]) => void;
  setTabs: (tabs: unknown[]) => void;
};

export type QuantLabStore = ReturnType<typeof createQuantLabStore>;

export function createQuantLabStore(
  initial?: Partial<QuantLabStoreState>
) {
  return createStore<QuantLabStoreState & QuantLabStoreActions>((set) => ({
    tabs: initial?.tabs ?? [],
    activeTabId: initial?.activeTabId ?? null,
    selectedRunIds: initial?.selectedRunIds ?? [],
    setActiveTabId: (activeTabId) => set({ activeTabId }),
    setSelectedRunIds: (selectedRunIds) => set({ selectedRunIds }),
    setTabs: (tabs) => set({ tabs }),
  }));
}
