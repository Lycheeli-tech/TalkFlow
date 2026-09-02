"use client";

import { createContext, ReactNode, useCallback, useContext, useMemo, useSyncExternalStore } from "react";

import { getStoredLocale, InterfaceLocale, INTERFACE_LOCALE_STORAGE_KEY } from "@/lib/i18n";

type InterfaceLocaleContextValue = {
  locale: InterfaceLocale;
  setLocale: (locale: InterfaceLocale) => void;
};

const InterfaceLocaleContext = createContext<InterfaceLocaleContextValue | null>(null);
const LOCALE_CHANGE_EVENT = "fluentloop-interface-locale-change";

function subscribeToLocale(onStoreChange: () => void) {
  window.addEventListener("storage", onStoreChange);
  window.addEventListener(LOCALE_CHANGE_EVENT, onStoreChange);
  return () => {
    window.removeEventListener("storage", onStoreChange);
    window.removeEventListener(LOCALE_CHANGE_EVENT, onStoreChange);
  };
}

export function InterfaceLocaleProvider({ children }: { children: ReactNode }) {
  const locale = useSyncExternalStore<InterfaceLocale>(
    subscribeToLocale,
    getStoredLocale,
    (): InterfaceLocale => "en",
  );

  const setLocale = useCallback((nextLocale: InterfaceLocale) => {
    sessionStorage.setItem(INTERFACE_LOCALE_STORAGE_KEY, nextLocale);
    window.dispatchEvent(new Event(LOCALE_CHANGE_EVENT));
  }, []);

  const value = useMemo(() => ({ locale, setLocale }), [locale, setLocale]);
  return <InterfaceLocaleContext.Provider value={value}>{children}</InterfaceLocaleContext.Provider>;
}

export function useInterfaceLocale() {
  const context = useContext(InterfaceLocaleContext);
  if (!context) throw new Error("useInterfaceLocale must be used within InterfaceLocaleProvider.");
  return context;
}
