import en from "@/locales/en.json";
import zhCN from "@/locales/zh-CN.json";

export type InterfaceLocale = "en" | "zh-CN";

const catalogs = {
  en,
  "zh-CN": zhCN,
} as const;

export function getMessages(locale: InterfaceLocale) {
  return catalogs[locale];
}

