import type { Metadata } from "next";
import Link from "next/link";
import { legalDocuments, legalDownloadHref } from "@/data/legal-documents";
import { leadForm } from "@/data/texts/landing";
import { privacyPageDescription, siteMetadata } from "@/data/seo/site-metadata";

const pageTitle = "Политика конфиденциальности";
const { h1, paragraphs } = legalDocuments.privacy;

export const metadata: Metadata = {
  title: pageTitle,
  description: privacyPageDescription,
  alternates: { canonical: "/privacy" },
  openGraph: {
    type: "website",
    locale: "ru_RU",
    url: "/privacy",
    siteName: siteMetadata.openGraphSiteName,
    title: `${pageTitle} · ${siteMetadata.titleTemplateSuffix}`,
    description: privacyPageDescription,
  },
  twitter: {
    card: "summary",
    title: `${pageTitle} · ${siteMetadata.titleTemplateSuffix}`,
    description: privacyPageDescription,
  },
  robots: { index: true, follow: true },
};

export default function PrivacyPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16">
      <Link
        href="/"
        className="text-sm font-medium text-primary underline-offset-4 hover:underline"
      >
        ← На главную
      </Link>
      <h1 className="mt-8 font-serif text-3xl font-semibold text-foreground">
        {h1}
      </h1>
      <div className="prose prose-neutral mt-8 max-w-none space-y-4 text-sm leading-relaxed text-muted-foreground">
        {paragraphs.map((text, i) => (
          <p key={i}>{text}</p>
        ))}
      </div>
      <p className="mt-10 text-sm">
        <a
          href={legalDownloadHref.privacy}
          download
          className="font-medium text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded-sm"
        >
          {leadForm.legalPageDownloadCta}
        </a>
      </p>
    </div>
  );
}
