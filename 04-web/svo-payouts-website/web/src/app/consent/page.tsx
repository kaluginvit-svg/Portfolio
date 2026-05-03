import type { Metadata } from "next";
import Link from "next/link";
import { legalDocuments, legalDownloadHref } from "@/data/legal-documents";
import { leadForm } from "@/data/texts/landing";
import { consentPageDescription, siteMetadata } from "@/data/seo/site-metadata";

const pageTitle = "Согласие на обработку персональных данных";
const { h1, paragraphs } = legalDocuments.consent;

export const metadata: Metadata = {
  title: pageTitle,
  description: consentPageDescription,
  alternates: { canonical: "/consent" },
  openGraph: {
    type: "website",
    locale: "ru_RU",
    url: "/consent",
    siteName: siteMetadata.openGraphSiteName,
    title: `${pageTitle} · ${siteMetadata.titleTemplateSuffix}`,
    description: consentPageDescription,
  },
  twitter: {
    card: "summary",
    title: `${pageTitle} · ${siteMetadata.titleTemplateSuffix}`,
    description: consentPageDescription,
  },
  robots: { index: true, follow: true },
};

export default function ConsentPage() {
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
          href={legalDownloadHref.consent}
          download
          className="font-medium text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded-sm"
        >
          {leadForm.legalPageDownloadCta}
        </a>
      </p>
    </div>
  );
}
