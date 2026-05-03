import { GoogleAnalytics } from "@next/third-parties/google";

type Props = {
  gaId: string;
};

/**
 * GA4 через @next/third-parties (gtag.js + учёт переходов в App Router).
 * ID только из env; невалидный G-XXXXXXXXXX не ренерим.
 */
export function GoogleAnalyticsApp({ gaId }: Props) {
  const id = gaId.trim();
  if (!/^G-[A-Z0-9]+$/i.test(id)) return null;
  return <GoogleAnalytics gaId={id} />;
}
