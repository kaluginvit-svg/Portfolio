"use client";

import { motion } from "framer-motion";
import {
  AlertCircle,
  Building2,
  ClipboardCheck,
  FileStack,
  Layers,
  MapPin,
  Shield,
  Landmark,
  HeartHandshake,
} from "lucide-react";
import {
  documentsIntent,
  ifNotPaidIntent,
  paymentsIntent,
  payoutStructureIntent,
  submittedCasesIntent,
  whereToApplyIntent,
} from "@/data/texts/intent-sections";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const stroke = 1.875;

const fade = {
  initial: { opacity: 0, y: 14 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "-50px" },
  transition: { duration: 0.42, ease: [0.22, 1, 0.36, 1] as const },
};

const paymentStrips = [
  "ds-card-strip--federal",
  "ds-card-strip--monthly",
  "ds-card-strip--regional",
  "ds-card-strip--review",
] as const;

export function PaymentsIntentSection() {
  const blocks = [
    { ...paymentsIntent.federal, icon: Landmark },
    { ...paymentsIntent.monthly, icon: Layers },
    { ...paymentsIntent.regional, icon: MapPin },
    { ...paymentsIntent.verification, icon: Shield },
  ] as const;

  return (
    <section
      id="payments"
      aria-labelledby="payments-intent-heading"
      className="ds-section-y scroll-mt-[4.5rem] border-b border-[var(--cool-border)] bg-[var(--main-bg)] px-4 min-[360px]:px-5 lg:px-8"
    >
      <div className="mx-auto max-w-6xl">
        <motion.div {...fade} className="mx-auto max-w-3xl text-center lg:mx-0 lg:text-left">
          <p className="ds-section-kicker">{paymentsIntent.kicker}</p>
          <h2 id="payments-intent-heading" className="ds-h2 mt-3">
            {paymentsIntent.h2}
          </h2>
          <p className="ds-body mt-4">{paymentsIntent.intro}</p>
        </motion.div>
        <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:gap-6">
          {blocks.map((b, i) => (
            <motion.div
              key={b.title}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ delay: i * 0.05, duration: 0.4 }}
            >
              <Card
                className={cn(
                  "ds-spec-card-hover relative h-full overflow-hidden pt-1 shadow-[var(--shadow-spec-card)]",
                  "ds-card-strip",
                  paymentStrips[i],
                )}
              >
                <CardContent className="p-5 sm:p-6 md:pt-5">
                  <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-[var(--soft-blue-bg)] text-[var(--deep-blue)]">
                    <b.icon className="h-5 w-5" strokeWidth={stroke} aria-hidden />
                  </div>
                  <h3 className="ds-h3 !text-[1.125rem] md:!text-[1.25rem]">{b.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-[var(--text-secondary)] md:text-[0.9375rem]">
                    {b.body}
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

export function PayoutStructureIntentSection() {
  return (
    <section
      id="payout-structure"
      aria-labelledby="payout-structure-heading"
      className="ds-section-y scroll-mt-[4.5rem] border-b border-[var(--cool-border)] bg-[var(--section-bg)] px-4 min-[360px]:px-5 lg:px-8"
    >
      <div className="mx-auto max-w-6xl">
        <motion.div {...fade} className="mx-auto max-w-3xl text-center lg:mx-0 lg:text-left">
          <p className="ds-section-kicker">{payoutStructureIntent.kicker}</p>
          <h2 id="payout-structure-heading" className="ds-h2 mt-3 text-[var(--deep-blue)]">
            {payoutStructureIntent.h2}
          </h2>
          <p className="ds-body mt-4">{payoutStructureIntent.intro}</p>
        </motion.div>
        <ol className="mt-10 space-y-5">
          {payoutStructureIntent.layers.map((layer, i) => (
            <motion.li
              key={layer.title}
              initial={{ opacity: 0, x: -8 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-30px" }}
              transition={{ delay: i * 0.06, duration: 0.38 }}
            >
              <Card className="ds-spec-card-hover border-[var(--cool-border)] shadow-[var(--shadow-spec-card)]">
                <CardContent className="flex gap-4 p-5 sm:p-6">
                  <span
                    className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--deep-blue)] font-serif text-sm font-semibold text-white"
                    aria-hidden
                  >
                    {i + 1}
                  </span>
                  <div>
                    <h3 className="text-base font-semibold text-[var(--text-primary)]">{layer.title}</h3>
                    <p className="mt-1.5 text-sm leading-relaxed text-[var(--text-secondary)] md:text-[0.9375rem]">
                      {layer.body}
                    </p>
                  </div>
                </CardContent>
              </Card>
            </motion.li>
          ))}
        </ol>
      </div>
    </section>
  );
}

export function WhereToApplyIntentSection() {
  return (
    <section
      id="where-to-apply"
      aria-labelledby="where-to-apply-heading"
      className="ds-section-y scroll-mt-[4.5rem] border-b border-[var(--cool-border)] bg-[var(--main-bg)] px-4 min-[360px]:px-5 lg:px-8"
    >
      <div className="mx-auto max-w-6xl">
        <motion.div {...fade} className="mx-auto max-w-3xl text-center lg:mx-0 lg:text-left">
          <p className="ds-section-kicker">{whereToApplyIntent.kicker}</p>
          <h2 id="where-to-apply-heading" className="ds-h2 mt-3">
            {whereToApplyIntent.h2}
          </h2>
          <p className="ds-body mt-4">{whereToApplyIntent.intro}</p>
        </motion.div>
        <ul className="mt-10 grid gap-5 md:grid-cols-2 lg:grid-cols-3 lg:gap-6">
          {whereToApplyIntent.channels.map((ch, i) => (
            <motion.li
              key={ch.title}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ delay: i * 0.05, duration: 0.4 }}
            >
              <Card className="ds-spec-card-hover h-full border-[var(--cool-border)] shadow-[var(--shadow-spec-card)]">
                <CardContent className="p-5 sm:p-6">
                  <div className="mb-2 flex items-center gap-2 text-[var(--deep-blue)]">
                    <Building2 className="h-5 w-5 shrink-0" strokeWidth={stroke} aria-hidden />
                    <h3 className="font-serif text-base font-semibold text-[var(--text-primary)]">{ch.title}</h3>
                  </div>
                  <p className="text-sm leading-relaxed text-[var(--text-secondary)]">{ch.body}</p>
                </CardContent>
              </Card>
            </motion.li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export function IfNotPaidIntentSection() {
  return (
    <section
      id="if-not-paid"
      aria-labelledby="if-not-paid-heading"
      className="ds-section-y scroll-mt-[4.5rem] border-b border-[var(--cool-border)] bg-[var(--section-bg)] px-4 min-[360px]:px-5 lg:px-8"
    >
      <div className="mx-auto max-w-6xl">
        <motion.div {...fade} className="mx-auto max-w-3xl text-center lg:mx-0 lg:text-left">
          <p className="ds-section-kicker">{ifNotPaidIntent.kicker}</p>
          <h2 id="if-not-paid-heading" className="ds-h2 mt-3">
            {ifNotPaidIntent.h2}
          </h2>
          <p className="ds-body mt-4">{ifNotPaidIntent.intro}</p>
        </motion.div>
        <div className="mt-10 space-y-5">
          {ifNotPaidIntent.cases.map((c, i) => (
            <motion.div
              key={c.title}
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-35px" }}
              transition={{ delay: i * 0.05, duration: 0.38 }}
              className="ds-analytic-module"
            >
              <div className="flex gap-4 pl-1">
                <AlertCircle
                  className="mt-0.5 h-5 w-5 shrink-0 text-[var(--status-warning)]"
                  strokeWidth={stroke}
                  aria-hidden
                />
                <div>
                  <h3 className="font-semibold text-[var(--text-primary)]">{c.title}</h3>
                  <p className="mt-1.5 text-sm leading-relaxed text-[var(--text-secondary)] md:text-[0.9375rem]">
                    {c.body}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
        <motion.p
          {...fade}
          className="mx-auto mt-10 max-w-3xl text-center text-sm leading-relaxed text-[var(--text-secondary)] lg:text-left"
        >
          {ifNotPaidIntent.closing}
        </motion.p>
      </div>
    </section>
  );
}

export function SubmittedCasesIntentSection() {
  return (
    <section
      id="stuck-cases"
      aria-labelledby="submitted-cases-heading"
      className="ds-section-y scroll-mt-[4.5rem] border-b border-[var(--cool-border)] bg-[var(--main-bg)] px-4 min-[360px]:px-5 lg:px-8"
    >
      <div className="mx-auto max-w-6xl">
        <motion.div {...fade} className="mx-auto max-w-3xl text-center lg:mx-0 lg:text-left">
          <p className="ds-section-kicker">{submittedCasesIntent.kicker}</p>
          <h2 id="submitted-cases-heading" className="ds-h2 mt-3 text-[var(--deep-blue)]">
            {submittedCasesIntent.h2}
          </h2>
          <p className="ds-body mt-4">{submittedCasesIntent.intro}</p>
        </motion.div>

        <div className="mt-10 grid gap-6 lg:grid-cols-3 lg:gap-8">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="ds-analytic-module lg:col-span-1"
          >
            <div className="flex items-start gap-3 pl-1">
              <HeartHandshake
                className="h-5 w-5 shrink-0 text-[var(--deep-blue)]"
                strokeWidth={stroke}
                aria-hidden
              />
              <div>
                <h3 className="font-serif text-lg font-semibold text-[var(--text-primary)]">
                  {submittedCasesIntent.audience.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-[var(--text-secondary)]">
                  {submittedCasesIntent.audience.body}
                </p>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.05 }}
            className="ds-analytic-module lg:col-span-2"
          >
            <div className="flex items-start gap-3 pl-1">
              <ClipboardCheck
                className="h-5 w-5 shrink-0 text-[var(--deep-blue)]"
                strokeWidth={stroke}
                aria-hidden
              />
              <div>
                <h3 className="font-serif text-lg font-semibold text-[var(--text-primary)]">
                  {submittedCasesIntent.dataNeeded.title}
                </h3>
                <ul className="mt-3 list-inside list-disc space-y-2 text-sm leading-relaxed text-[var(--text-secondary)] marker:text-[var(--deep-blue)]">
                  {submittedCasesIntent.dataNeeded.items.map((item) => (
                    <li key={item} className="pl-1">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.08 }}
          className="ds-analytic-module mt-6"
        >
          <h3 className="pl-1 font-serif text-lg font-semibold text-[var(--text-primary)]">
            {submittedCasesIntent.firstStage.title}
          </h3>
          <p className="mt-2 pl-1 text-sm leading-relaxed text-[var(--text-secondary)] md:text-base">
            {submittedCasesIntent.firstStage.body}
          </p>
        </motion.div>

        <div className="mt-10 grid gap-5 sm:grid-cols-3 lg:gap-6">
          {submittedCasesIntent.supportCards.map((card, i) => (
            <motion.div
              key={card.title}
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-30px" }}
              transition={{ delay: 0.1 + i * 0.05 }}
            >
              <Card
                className={cn(
                  "ds-spec-card-hover relative h-full overflow-hidden pt-1 shadow-[var(--shadow-spec-card)]",
                  "ds-card-strip ds-card-strip--review",
                )}
              >
                <CardContent className="p-5">
                  <h3 className="font-semibold text-[var(--text-primary)]">{card.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-[var(--text-secondary)]">{card.body}</p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        <p className="mx-auto mt-10 max-w-3xl text-center text-sm leading-relaxed text-[var(--text-secondary)] lg:text-left">
          {submittedCasesIntent.footer}
        </p>
      </div>
    </section>
  );
}

export function DocumentsIntentSection() {
  return (
    <section
      id="documents"
      aria-labelledby="documents-intent-heading"
      className="ds-section-y scroll-mt-[4.5rem] border-b border-[var(--cool-border)] bg-[var(--section-bg)] px-4 min-[360px]:px-5 lg:px-8"
    >
      <div className="mx-auto max-w-6xl">
        <motion.div {...fade} className="mx-auto max-w-3xl text-center lg:mx-0 lg:text-left">
          <p className="ds-section-kicker">{documentsIntent.kicker}</p>
          <h2 id="documents-intent-heading" className="ds-h2 mt-3">
            {documentsIntent.h2}
          </h2>
          <p className="ds-body mt-4">{documentsIntent.intro}</p>
        </motion.div>
        <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:gap-6">
          {documentsIntent.groups.map((g, i) => (
            <motion.div
              key={g.title}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ delay: i * 0.05, duration: 0.4 }}
            >
              <Card className="ds-spec-card-hover h-full border-[var(--cool-border)] shadow-[var(--shadow-spec-card)]">
                <CardContent className="flex gap-4 p-5 sm:p-6">
                  <FileStack
                    className="mt-0.5 h-5 w-5 shrink-0 text-[var(--deep-blue)]"
                    strokeWidth={stroke}
                    aria-hidden
                  />
                  <div>
                    <h3 className="font-semibold text-[var(--text-primary)]">{g.title}</h3>
                    <p className="mt-2 text-sm leading-relaxed text-[var(--text-secondary)]">{g.body}</p>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
        <motion.p
          {...fade}
          className="mx-auto mt-8 max-w-3xl rounded-xl border border-dashed border-[var(--cool-border)] bg-white px-4 py-3 text-center text-sm leading-relaxed text-[var(--text-secondary)] lg:text-left"
        >
          {documentsIntent.note}
        </motion.p>
      </div>
    </section>
  );
}
