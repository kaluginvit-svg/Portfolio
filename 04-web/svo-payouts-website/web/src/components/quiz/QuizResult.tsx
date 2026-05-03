"use client";

import { motion } from "framer-motion";
import { useEffect } from "react";
import {
  Banknote,
  Building2,
  ClipboardList,
  HeartHandshake,
  MapPin,
  PiggyBank,
  Route,
  Shield,
  type LucideIcon,
} from "lucide-react";
import { formatRub, getRecipientsCount } from "@/lib/calculator";
import { computeDelayLossRub } from "@/lib/calculator/delay-loss";
import { buildPayoutBreakdownView } from "@/lib/calculator/payout-view";
import { getPersonalAccents } from "@/lib/quiz/personal-accents";
import { getEstimatedWaitingMonths } from "@/lib/quiz/waiting-months";
import { resultSectionCopy } from "@/data/texts/result-section";
import { useCountUp } from "@/hooks/use-count-up";
import type { QuizAnswers } from "@/types/quiz";
import type { RegionalCatalogStatus } from "@/types/payouts";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { trackEvent } from "@/lib/analytics/track";
import { cn } from "@/lib/utils";

const iconStroke = 1.875;

type Props = {
  answers: QuizAnswers;
  onAgain: () => void;
  onLead: () => void;
  onPersonalBreakdown: () => void;
};

function regionalBadge(status: RegionalCatalogStatus) {
  const styles: Record<RegionalCatalogStatus, string> = {
    confirmed: "ds-badge ds-badge-confirmed",
    partial: "ds-badge ds-badge-partial",
    needs_verification: "ds-badge ds-badge-review",
    no_data: "ds-badge border border-[var(--cool-border)] bg-[var(--neutral-surface)] text-[var(--text-secondary)]",
  };
  const labels: Record<RegionalCatalogStatus, string> = {
    confirmed: resultSectionCopy.regionalStatusConfirmed,
    partial: resultSectionCopy.regionalStatusPartial,
    needs_verification: resultSectionCopy.regionalStatusNeedsVerification,
    no_data: resultSectionCopy.regionalStatusNoData,
  };
  return (
    <span className={cn("shrink-0 font-semibold normal-case", styles[status])}>{labels[status]}</span>
  );
}

export function QuizResult({
  answers,
  onAgain,
  onLead,
  onPersonalBreakdown,
}: Props) {
  const recipientsCount = getRecipientsCount(answers);
  const view = buildPayoutBreakdownView(answers);
  const fresh = view.freshMeta;
  const federalTotal = view.federalOneTimeTotal;
  const personalShareNumeric =
    fresh?.personalShareRub ?? federalTotal / recipientsCount;
  const headlineNumeric = fresh?.headlineAmountNumeric ?? federalTotal;
  const accents = getPersonalAccents(answers);
  const animatedTotal = useCountUp(headlineNumeric, 1200);
  const animatedShare = useCountUp(
    fresh?.shareRequiresClarification ? 0 : personalShareNumeric,
    1400,
  );
  const sumDisplay = new Intl.NumberFormat("ru-RU", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(animatedTotal);
  const shareDisplay = new Intl.NumberFormat("ru-RU", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(animatedShare);

  const waitMonths = getEstimatedWaitingMonths(answers);
  const delayRub = computeDelayLossRub(
    federalTotal,
    fresh?.shareRequiresClarification ? federalTotal / Math.max(1, recipientsCount) : personalShareNumeric,
    waitMonths,
  );
  const delayFamilyRub = delayRub?.delayFamilyRub ?? null;
  const delayShareRub = delayRub?.delayShareRub ?? null;

  useEffect(() => {
    trackEvent("result_view", { flow_mode: "fresh" });
  }, []);

  return (
    <motion.div
      id="quiz-result"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="scroll-mt-24"
      role="region"
      aria-label={resultSectionCopy.ariaRegionLabel}
    >
      <div className="relative -mx-4 -mb-6 -mt-2 bg-[var(--neutral-surface)] px-4 py-14 min-[360px]:-mx-5 min-[360px]:px-5 sm:-mx-6 sm:px-6 md:py-20 lg:-mx-8 lg:px-8 lg:py-28">
        <div className="mx-auto max-w-4xl space-y-10 lg:space-y-12">
          <div className="ds-result-highlight relative overflow-hidden px-6 py-10 sm:px-10 sm:py-12 md:px-12 md:py-14">
            <div
              className="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full bg-[radial-gradient(circle,rgb(22_58_99/0.06),transparent_68%)]"
              aria-hidden
            />
            <div
              className="pointer-events-none absolute -bottom-24 -left-16 h-56 w-56 rounded-full bg-[radial-gradient(circle,rgb(179_38_46/0.05),transparent_65%)]"
              aria-hidden
            />

            <div className="relative mx-auto mb-5 h-1 max-w-[7rem] rounded-full bg-gradient-to-r from-[#163A63] to-[#B3262E] sm:mx-0" />

            <p className="relative text-center text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--text-secondary)] sm:text-left">
              {resultSectionCopy.kicker}
            </p>
            <p className="relative mx-auto mt-4 max-w-prose text-center font-serif text-lg font-semibold leading-snug text-[var(--text-primary)] sm:mx-0 sm:text-left sm:text-xl md:text-2xl">
              {resultSectionCopy.intro}
            </p>

            <div className="relative mt-6 rounded-xl border border-[var(--light-blue-divider)] bg-white/90 p-4 sm:p-5">
              <p className="text-xs font-semibold uppercase tracking-wider text-[var(--deep-blue)]">
                {resultSectionCopy.intentBridgeTitle}
              </p>
              <p className="mt-2 text-sm leading-relaxed text-[var(--text-secondary)] sm:text-[0.9375rem]">
                {resultSectionCopy.intentBridge}
              </p>
            </div>

            <div className="relative mt-10 text-center sm:text-left">
              <p className="text-xs font-medium text-[var(--text-secondary)] sm:text-sm">
                {fresh?.headlinePrefix ?? resultSectionCopy.sumLabelFederal}
              </p>
              <p
                className="mt-3 font-serif text-[clamp(2.25rem,7vw,4rem)] font-semibold leading-none tracking-tight text-[var(--deep-blue)]"
                aria-live="polite"
              >
                {fresh?.headlineMode === "up_to" ? (
                  <span className="mr-1 align-baseline text-[0.42em] font-semibold text-[var(--deep-blue)]">
                    до{" "}
                  </span>
                ) : null}
                {fresh?.headlineMode === "from" ? (
                  <span className="mr-1 align-baseline text-[0.42em] font-semibold text-[var(--deep-blue)]">
                    от{" "}
                  </span>
                ) : null}
                <span className="tabular-nums">{sumDisplay}</span>
                <span className="ml-1 align-baseline text-[0.42em] font-semibold text-[var(--deep-blue)]">
                  ₽
                </span>
              </p>
              {fresh ? (
                <div className="mt-4 space-y-2">
                  <p className="text-sm font-semibold text-[var(--deep-blue)]">{fresh.precisionLabel}</p>
                  {fresh.clarificationNote ? (
                    <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
                      {fresh.clarificationNote}
                    </p>
                  ) : null}
                  {fresh.regionalNote ? (
                    <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
                      {fresh.regionalNote}
                    </p>
                  ) : null}
                </div>
              ) : null}
            </div>

            <div className="relative mt-10 rounded-xl border border-[var(--cool-border)] bg-white p-5 sm:p-6">
              <div className="flex items-start gap-4">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[var(--soft-blue-bg)] text-[var(--deep-blue)]">
                  <HeartHandshake className="h-6 w-6" strokeWidth={iconStroke} aria-hidden />
                </div>
                <div>
                  <p className="text-sm font-semibold text-[var(--text-primary)] md:text-base">
                    {resultSectionCopy.shareTitle}
                  </p>
                  <p className="mt-2 text-sm leading-relaxed text-[var(--text-secondary)] md:text-[0.9375rem]">
                    {resultSectionCopy.shareBodyPrefix}{" "}
                    {fresh?.shareRequiresClarification ? (
                      <span className="font-semibold text-[var(--text-primary)]">
                        требует уточнений
                      </span>
                    ) : (
                      <span className="font-semibold tabular-nums text-[var(--text-primary)]">
                        {shareDisplay} ₽
                      </span>
                    )}{" "}
                    {fresh?.shareRequiresClarification && answers.freshRecipientsCount === "unknown"
                      ? "Число претендентов в расчёте не задано."
                      : `${resultSectionCopy.shareBodySuffix} ${recipientsCount}.`}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <section aria-labelledby="federal-breakdown-heading" className="space-y-5">
            <div className="ds-spec-card ds-card-strip ds-card-strip--federal ds-spec-card-hover space-y-4 !pt-5 md:!pt-6">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                <h3 id="federal-breakdown-heading" className="ds-h3 text-balance sm:text-left">
                  {resultSectionCopy.breakdownTitle}
                </h3>
                <span className="hidden text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] sm:inline">
                  Федеральный уровень
                </span>
              </div>
              <p className="text-sm leading-relaxed text-[var(--text-secondary)] md:text-[0.9375rem]">
                {resultSectionCopy.breakdownLead}
              </p>
              <ul className="grid gap-5 sm:grid-cols-2" role="list">
                {view.federalOneTimeLines.map((line, i) => (
                  <motion.li
                    key={line.id}
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{
                      delay: 0.1 + i * 0.08,
                      duration: 0.45,
                      ease: [0.22, 1, 0.36, 1],
                    }}
                  >
                    <BreakdownRow
                      icon={
                        line.id === "presidential"
                          ? Building2
                          : line.id === "benefit306"
                            ? Banknote
                            : Shield
                      }
                      title={
                        line.id === "presidential"
                          ? resultSectionCopy.rowPresidential
                          : line.id === "benefit306"
                            ? resultSectionCopy.rowBenefit
                            : resultSectionCopy.rowInsurance
                      }
                      amount={formatRub(line.amountRub)}
                    />
                  </motion.li>
                ))}
              </ul>
            </div>
          </section>

          <section aria-labelledby="monthly-heading" className="space-y-5">
            <div className="ds-spec-card ds-card-strip ds-card-strip--monthly ds-spec-card-hover !pt-5 md:!pt-6">
              <h3 id="monthly-heading" className="ds-h3 text-balance text-center sm:text-left">
                {resultSectionCopy.monthlyTitle}
              </h3>
              <p className="mt-3 text-sm leading-relaxed text-[var(--text-secondary)] sm:text-[0.9375rem]">
                {resultSectionCopy.monthlyLead}
              </p>
              <ul className="mt-6 space-y-4" role="list">
                {view.monthlyLines.map((line, i) => (
                  <motion.li
                    key={line.id}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.15 + i * 0.07, duration: 0.42 }}
                  >
                    <Card className="rounded-xl border border-[var(--cool-border)] bg-[var(--neutral-surface)] shadow-none">
                      <CardContent className="flex gap-4 p-5">
                        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[var(--soft-blue-bg)] text-[var(--status-info)]">
                          <PiggyBank className="h-5 w-5" strokeWidth={iconStroke} aria-hidden />
                        </div>
                        <div className="min-w-0">
                          <p className="text-sm font-semibold text-[var(--text-primary)]">{line.title}</p>
                          {line.amountRub != null ? (
                            <p className="mt-1 font-serif text-base font-semibold tabular-nums text-[var(--text-primary)] sm:text-lg">
                              {fresh && line.id === "child_monthly_total" && fresh.monthlyPrefix ? (
                                <span className="inline font-semibold">{fresh.monthlyPrefix}</span>
                              ) : null}
                              {formatRub(line.amountRub)}
                            </p>
                          ) : null}
                          <p className="mt-1.5 text-sm leading-relaxed text-[var(--text-secondary)]">
                            {line.description}
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.li>
                ))}
              </ul>
            </div>
          </section>

          <section
            aria-labelledby="regional-heading"
            aria-live="polite"
            className="space-y-5"
          >
            <div
              className={cn(
                "ds-regional-surface relative overflow-hidden pt-1",
                "before:absolute before:left-0 before:right-0 before:top-0 before:z-10 before:h-1 before:rounded-t-[23px] before:bg-[var(--accent-red)]",
              )}
            >
              <div className="p-6 sm:p-8">
                <div className="flex flex-col gap-5 border-b border-[color-mix(in_srgb,var(--accent-red)_18%,var(--cool-border))] pb-6 sm:flex-row sm:items-start sm:justify-between">
                  <div className="flex items-start gap-4">
                    <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border border-[color-mix(in_srgb,var(--accent-red)_25%,var(--cool-border))] bg-white text-[var(--accent-red)] shadow-sm">
                      <MapPin className="h-7 w-7" strokeWidth={iconStroke} aria-hidden />
                    </div>
                    <div>
                      <h3
                        id="regional-heading"
                        className="font-serif text-xl font-semibold tracking-tight text-[var(--text-primary)] md:text-2xl"
                      >
                        {resultSectionCopy.regionalTitle}
                      </h3>
                      {view.regional.regionName ? (
                        <p className="mt-2 text-sm text-[var(--text-secondary)]">
                          Регион в расчёте:{" "}
                          <span className="font-semibold text-[var(--text-primary)]">
                            {view.regional.regionName}
                          </span>
                        </p>
                      ) : null}
                      <p className="mt-3 text-sm leading-relaxed text-[var(--text-secondary)] md:text-[0.9375rem]">
                        {resultSectionCopy.regionalLead}
                      </p>
                    </div>
                  </div>
                  <div className="flex flex-col items-start gap-2 sm:items-end">
                    {regionalBadge(view.regional.blockStatus)}
                    {view.regional.catalogLastUpdated ? (
                      <p className="text-xs text-[var(--text-secondary)] sm:text-right">
                        {resultSectionCopy.regionalCatalogUpdated}:{" "}
                        {new Intl.DateTimeFormat("ru-RU", {
                          dateStyle: "medium",
                        }).format(new Date(view.regional.catalogLastUpdated))}
                      </p>
                    ) : null}
                  </div>
                </div>

                <div className="mt-6 space-y-4">
                  {view.regional.needsManualCheck && view.regional.lines.length === 0 ? (
                    <div className="flex gap-3 rounded-xl border border-dashed border-[var(--deep-blue)]/25 bg-white p-4 sm:p-5">
                      <Route
                        className="mt-0.5 h-5 w-5 shrink-0 text-[var(--deep-blue)]"
                        strokeWidth={iconStroke}
                        aria-hidden
                      />
                      <p className="text-sm leading-relaxed text-[var(--text-primary)]">
                        {resultSectionCopy.regionalManual}
                      </p>
                    </div>
                  ) : null}

                  {view.regional.disclaimer ? (
                    <p className="flex gap-2 text-xs leading-relaxed text-[var(--text-secondary)] sm:text-sm">
                      <span
                        className="mt-0.5 inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--accent-red)]/75"
                        aria-hidden
                      />
                      <span>{view.regional.disclaimer}</span>
                    </p>
                  ) : null}

                  {view.regional.catalogIncomplete && view.regional.lines.length > 0 ? (
                    <p className="text-xs text-[var(--text-secondary)] sm:text-sm">
                      {resultSectionCopy.regionalPartialNote}
                    </p>
                  ) : null}

                  <ul className="space-y-4" role="list">
                    {view.regional.lines.map((line, i) => (
                      <motion.li
                        key={line.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.12 + i * 0.06 }}
                      >
                        <Card
                          className={cn(
                            "rounded-xl border shadow-none",
                            line.isPartial
                              ? "border-[color-mix(in_srgb,var(--status-warning)_35%,var(--cool-border))] bg-[#fffbeb]"
                              : "border-[var(--cool-border)] bg-white",
                          )}
                        >
                          <CardContent className="space-y-1.5 p-4 sm:p-5">
                            <div className="flex flex-wrap items-center gap-2">
                              <p className="text-sm font-semibold text-[var(--text-primary)]">{line.title}</p>
                              {line.isPartial ? (
                                <span className="ds-badge ds-badge-partial text-[11px]">Частично</span>
                              ) : (
                                <span className="ds-badge ds-badge-info text-[11px]">В расчёте</span>
                              )}
                            </div>
                            {line.amountRub != null ? (
                              <p className="font-serif text-base font-semibold tabular-nums sm:text-lg">
                                {formatRub(line.amountRub)}
                              </p>
                            ) : (
                              <p className="text-sm text-[var(--text-secondary)]">
                                Сумма не унифицирована в каталоге
                              </p>
                            )}
                            {line.recipientsNote ? (
                              <p className="text-xs text-[var(--text-secondary)]">{line.recipientsNote}</p>
                            ) : null}
                            {line.description ? (
                              <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
                                {line.description}
                              </p>
                            ) : null}
                          </CardContent>
                        </Card>
                      </motion.li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </section>

          <section aria-labelledby="other-heading" className="space-y-5">
            <div className="ds-spec-card ds-card-strip ds-card-strip--review ds-spec-card-hover !pt-5 md:!pt-6">
              <h3 id="other-heading" className="ds-h3 text-balance text-center sm:text-left">
                {resultSectionCopy.otherTitle}
              </h3>
              <ul className="mt-6 space-y-4" role="list">
                {view.otherMeasures.map((m, i) => (
                  <motion.li
                    key={m.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.08 + i * 0.06 }}
                  >
                    <Card className="rounded-xl border border-[var(--cool-border)] bg-white shadow-none">
                      <CardContent className="flex gap-4 p-5">
                        <ClipboardList
                          className="mt-0.5 h-5 w-5 shrink-0 text-[var(--deep-blue)]"
                          strokeWidth={iconStroke}
                          aria-hidden
                        />
                        <div>
                          <p className="text-sm font-semibold text-[var(--text-primary)]">{m.title}</p>
                          <p className="mt-1.5 text-sm leading-relaxed text-[var(--text-secondary)]">
                            {m.description}
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.li>
                ))}
              </ul>
            </div>
          </section>

          {delayFamilyRub != null && delayShareRub != null && waitMonths != null ? (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.45 }}
              className="ds-delay-card p-6 sm:p-8"
              role="region"
              aria-labelledby="delay-heading"
            >
              <h3
                id="delay-heading"
                className="font-serif text-lg font-semibold text-[var(--text-primary)] md:text-xl"
              >
                {resultSectionCopy.delayTitle}
              </h3>
              <p className="mt-3 text-sm leading-relaxed text-[var(--text-secondary)] md:text-[0.9375rem]">
                {resultSectionCopy.delayIntro}
              </p>
              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                <div className="rounded-xl border border-[#f3d1d1] bg-white/80 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)]">
                    {resultSectionCopy.delayYourShare}
                  </p>
                  <p className="mt-2 font-serif text-xl font-semibold tabular-nums text-[var(--text-primary)]">
                    {formatRub(delayShareRub)}
                  </p>
                </div>
                <div className="rounded-xl border border-[#f3d1d1] bg-white/80 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)]">
                    {resultSectionCopy.delayFamily}
                  </p>
                  <p className="mt-2 font-serif text-xl font-semibold tabular-nums text-[var(--text-primary)]">
                    {formatRub(delayFamilyRub)}
                  </p>
                </div>
              </div>
              <p className="mt-4 text-xs leading-relaxed text-[var(--text-secondary)]">
                Ориентир примерно за {waitMonths} мес. ожидания и условных 1,2% в месяц.{" "}
                {resultSectionCopy.delayDisclaimer}
              </p>
            </motion.div>
          ) : null}

          {accents.length > 0 ? (
            <div className="ds-analytic-module space-y-5" role="list" aria-label={resultSectionCopy.diagnosticTitle}>
              <div className="flex items-center gap-2 pl-1">
                <Route className="h-5 w-5 text-[var(--deep-blue)]" strokeWidth={iconStroke} aria-hidden />
                <p className="font-serif text-base font-semibold text-[var(--text-primary)] md:text-lg">
                  {resultSectionCopy.diagnosticTitle}
                </p>
              </div>
              <ul className="space-y-3 pl-1">
                {accents.map((line, idx) => (
                  <motion.li
                    key={`accent-${idx}`}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 + idx * 0.06 }}
                    className="rounded-xl border border-[var(--light-blue-divider)] bg-[var(--neutral-surface)] px-4 py-3.5 text-sm leading-relaxed text-[var(--text-primary)] sm:px-5 sm:text-[0.9375rem]"
                  >
                    {line}
                  </motion.li>
                ))}
              </ul>
            </div>
          ) : null}

          <p className="text-center text-xs leading-relaxed text-[var(--text-secondary)] sm:text-left sm:text-sm">
            {resultSectionCopy.finalDisclaimer}
          </p>

          <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:gap-4">
            <Button type="button" variant="cta" size="touch" className="sm:min-w-[260px]" onClick={onPersonalBreakdown}>
              {resultSectionCopy.ctaPersonal}
            </Button>
            <Button type="button" variant="secondary" size="touch" className="sm:min-w-[200px]" onClick={onLead}>
              {resultSectionCopy.ctaContacts}
            </Button>
            <Button type="button" variant="outline" size="touch" className="sm:min-w-[180px]" onClick={onAgain}>
              {resultSectionCopy.ctaAgain}
            </Button>
          </div>

          <p className="text-center text-sm leading-relaxed text-[var(--text-secondary)] sm:text-left">
            {resultSectionCopy.ctaHint}
          </p>
        </div>
      </div>
    </motion.div>
  );
}

function BreakdownRow({
  icon: Icon,
  title,
  amount,
}: {
  icon: LucideIcon;
  title: string;
  amount: string;
}) {
  return (
    <Card className="ds-spec-card-hover h-full rounded-xl border border-[var(--cool-border)] bg-white shadow-[var(--shadow-spec-card)]">
      <CardContent className="flex h-full items-center gap-4 p-5">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[var(--soft-blue-bg)] text-[var(--deep-blue)]">
          <Icon className="h-6 w-6" strokeWidth={iconStroke} aria-hidden />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-secondary)]">
            {title}
          </p>
          <p className="mt-1 break-words font-serif text-base font-semibold tabular-nums text-[var(--text-primary)] sm:text-lg">
            {amount}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
