import en from "@/locales/en.json";
import zhCN from "@/locales/zh-CN.json";

export type InterfaceLocale = "en" | "zh-CN";

export const INTERFACE_LOCALE_STORAGE_KEY = "fluentloop_interface_locale";

const catalogs = {
  en,
  "zh-CN": zhCN,
} as const;

export function getMessages(locale: InterfaceLocale) {
  return catalogs[locale];
}

export function getStoredLocale(): InterfaceLocale {
  if (typeof window === "undefined") return "en";
  return sessionStorage.getItem(INTERFACE_LOCALE_STORAGE_KEY) === "zh-CN" ? "zh-CN" : "en";
}
