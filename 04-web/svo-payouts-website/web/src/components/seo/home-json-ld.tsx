import { faqItems } from "@/data/texts/landing";
import { siteMetadata } from "@/data/seo/site-metadata";
import { resolveSiteUrl } from "@/lib/site-url";

/**
 * JSON-LD главной: WebSite + FAQPage в @graph (один script, без дублирования контекста).
 */
export function HomeJsonLd() {
  const base = resolveSiteUrl();

  const data = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "WebSite",
        "@id": `${base}/#website`,
        url: base,
        name: siteMetadata.openGraphSiteName,
        description: siteMetadata.defaultDescription,
        inLanguage: "ru-RU",
      },
      {
        "@type": "FAQPage",
        "@id": `${base}/#faq`,
        isPartOf: { "@id": `${base}/#website` },
        mainEntity: faqItems.map((item) => ({
          "@type": "Question",
          name: item.q,
          acceptedAnswer: {
            "@type": "Answer",
            text: item.a,
          },
        })),
      },
    ],
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
    />
  );
}
