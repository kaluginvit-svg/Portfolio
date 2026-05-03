import Link from "next/link";
import { Mail, Phone } from "lucide-react";
import { legalDownloadHref } from "@/data/legal-documents";
import {
  footerDisclaimer,
  footerLegalNote,
  leadForm,
} from "@/data/texts/landing";

export function FooterSection() {
  return (
    <footer className="border-t border-[var(--cool-border)] bg-[color-mix(in_srgb,var(--primary-navy)_5%,var(--main-bg))] px-4 py-14 text-sm text-[var(--text-secondary)] min-[360px]:px-5 lg:px-8">
      <div className="mx-auto max-w-6xl space-y-10">
        <div className="grid gap-10 md:grid-cols-3 lg:gap-12">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-foreground/85">
              Контакты
            </p>
            <ul className="mt-4 space-y-3">
              <li>
                <a
                  className="inline-flex items-center gap-2 font-medium text-[var(--text-primary)] transition-colors hover:text-[var(--deep-blue)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--deep-blue)_30%,transparent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--main-bg)] rounded-md"
                  href="tel:+70000000000"
                >
                  <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--cool-border)] bg-white text-[var(--deep-blue)] shadow-sm">
                    <Phone className="h-4 w-4" strokeWidth={1.875} aria-hidden />
                  </span>
                  +7 (000) 000-00-00
                </a>
              </li>
              <li>
                <a
                  className="inline-flex items-center gap-2 font-medium text-[var(--text-primary)] transition-colors hover:text-[var(--deep-blue)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--deep-blue)_30%,transparent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--main-bg)] rounded-md"
                  href="mailto:hello@example.com"
                >
                  <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--cool-border)] bg-white text-[var(--deep-blue)] shadow-sm">
                    <Mail className="h-4 w-4" strokeWidth={1.875} aria-hidden />
                  </span>
                  hello@example.com
                </a>
              </li>
            </ul>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--text-primary)]">
              Документы
            </p>
            <ul className="mt-4 space-y-2">
              <li className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                <Link
                  href="/privacy"
                  className="text-[var(--text-primary)] underline-offset-4 transition-colors hover:text-[var(--deep-blue)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--deep-blue)_30%,transparent)] focus-visible:ring-offset-2 rounded-sm"
                >
                  Политика конфиденциальности
                </Link>
                <a
                  href={legalDownloadHref.privacy}
                  download
                  className="text-xs text-[var(--text-secondary)] underline-offset-4 transition-colors hover:text-[var(--deep-blue)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--deep-blue)_30%,transparent)] focus-visible:ring-offset-2 rounded-sm"
                >
                  {leadForm.legalDownloadShort}
                </a>
              </li>
              <li className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                <Link
                  href="/consent"
                  className="text-[var(--text-primary)] underline-offset-4 transition-colors hover:text-[var(--deep-blue)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--deep-blue)_30%,transparent)] focus-visible:ring-offset-2 rounded-sm"
                >
                  Согласие на обработку данных
                </Link>
                <a
                  href={legalDownloadHref.consent}
                  download
                  className="text-xs text-[var(--text-secondary)] underline-offset-4 transition-colors hover:text-[var(--deep-blue)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--deep-blue)_30%,transparent)] focus-visible:ring-offset-2 rounded-sm"
                >
                  {leadForm.legalDownloadShort}
                </a>
              </li>
            </ul>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--text-primary)]">
              Реквизиты
            </p>
            <p className="mt-4 max-w-xs text-xs leading-relaxed">
              ИП Иванов Иван Иванович · ИНН 000000000000 · ОГРНИП
              000000000000000 — замените на ваши данные.
            </p>
          </div>
        </div>
        <div className="space-y-3 border-t border-[var(--cool-border)] pt-8 text-xs leading-relaxed text-[var(--text-secondary)]">
          <p>{footerDisclaimer}</p>
          <p>{footerLegalNote}</p>
        </div>
      </div>
    </footer>
  );
}
