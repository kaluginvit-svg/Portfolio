import type { Metadata } from "next";
import { ThanksView } from "@/components/thanks/thanks-view";
import { siteMetadata } from "@/data/seo/site-metadata";

const thanksDescription =
  "Спасибо за обращение — ответ в ближайшее время по телефону или в мессенджере.";
const pageTitle = "Заявка отправлена";

export const metadata: Metadata = {
  title: pageTitle,
  description: thanksDescription,
  alternates: { canonical: "/thanks" },
  openGraph: {
    type: "website",
    locale: "ru_RU",
    url: "/thanks",
    siteName: siteMetadata.openGraphSiteName,
    title: `${pageTitle} · ${siteMetadata.titleTemplateSuffix}`,
    description: thanksDescription,
  },
  twitter: {
    card: "summary",
    title: `${pageTitle} · ${siteMetadata.titleTemplateSuffix}`,
    description: thanksDescription,
  },
  robots: {
    index: false,
    follow: false,
    googleBot: { index: false, follow: false },
  },
};

export default function ThanksPage() {
  const contactNote = process.env.CONTACT_TEXT?.trim() || null;
  return <ThanksView contactNote={contactNote} />;
}
