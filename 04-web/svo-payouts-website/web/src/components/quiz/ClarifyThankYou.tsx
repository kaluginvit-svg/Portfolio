"use client";

import { motion } from "framer-motion";
import { ClipboardList, HeartHandshake, Route } from "lucide-react";
import { clarifyQuizCopy } from "@/data/texts/clarify-quiz-copy";
import { Button } from "@/components/ui/button";

const stroke = 1.875;

type Props = {
  onLead: () => void;
  onStartCalculator: () => void;
  onAgain: () => void;
};

export function ClarifyThankYou({ onLead, onStartCalculator, onAgain }: Props) {
  return (
    <motion.div
      id="clarify-thanks"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      className="mx-auto w-full max-w-[860px] scroll-mt-24 space-y-8"
      role="region"
      aria-label="Опрос про документы завершён"
    >
      <div className="ds-quiz-card overflow-hidden">
        <div className="border-b border-[var(--light-blue-divider)] bg-[var(--neutral-surface)] px-6 py-6 md:px-10 md:py-8">
          <div className="flex flex-wrap items-center gap-3">
            <span className="ds-badge ds-badge-info border border-[var(--light-blue-divider)]">
              {clarifyQuizCopy.badge}
            </span>
            <span className="inline-flex items-center gap-1.5 text-xs font-medium text-[var(--text-secondary)]">
              <Route className="h-3.5 w-3.5 text-[var(--deep-blue)]" strokeWidth={stroke} aria-hidden />
              {clarifyQuizCopy.routePinned}
            </span>
          </div>
          <div className="mt-5 flex items-start gap-3">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[var(--soft-blue-bg)] text-[var(--deep-blue)]">
              <ClipboardList className="h-6 w-6" strokeWidth={stroke} aria-hidden />
            </div>
            <h2 className="font-serif text-xl font-semibold leading-snug text-pretty text-[var(--text-primary)] md:text-2xl">
              {clarifyQuizCopy.doneTitle}
            </h2>
          </div>
          <p className="mt-4 text-sm leading-relaxed text-[var(--text-secondary)] md:text-base">
            {clarifyQuizCopy.doneBody}
          </p>
        </div>

        <div className="space-y-4 bg-white px-6 py-8 md:px-10 md:py-10">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--text-secondary)]">
            Структура для дальнейшего разбора
          </p>
          <div className="grid gap-4 sm:grid-cols-2">
            {clarifyQuizCopy.diagnosticBlocks.map((block, i) => (
              <motion.div
                key={block.title}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.06 + i * 0.05 }}
                className="ds-analytic-module min-h-[8.5rem]"
              >
                <h3 className="pl-1 font-serif text-base font-semibold text-[var(--text-primary)]">
                  {block.title}
                </h3>
                <p className="mt-2 pl-1 text-sm leading-relaxed text-[var(--text-secondary)]">{block.body}</p>
              </motion.div>
            ))}
          </div>

          <div className="flex flex-col gap-3 pt-2 sm:flex-row sm:flex-wrap">
            <Button variant="cta" size="touch" className="sm:min-w-[12rem]" onClick={onLead}>
              <HeartHandshake className="h-5 w-5" strokeWidth={stroke} aria-hidden />
              {clarifyQuizCopy.ctaLead}
            </Button>
            <Button variant="outline" size="touch" className="sm:min-w-[12rem]" onClick={onStartCalculator}>
              {clarifyQuizCopy.ctaCalculator}
            </Button>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="w-full text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            onClick={onAgain}
          >
            {clarifyQuizCopy.again}
          </Button>
        </div>
      </div>
    </motion.div>
  );
}
