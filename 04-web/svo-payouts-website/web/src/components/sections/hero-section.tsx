"use client";

import { motion } from "framer-motion";
import { ArrowDown, CheckCircle2, Shield } from "lucide-react";
import { hero } from "@/data/texts/landing";
import { Button } from "@/components/ui/button";
import { useQuiz } from "@/contexts/quiz-context";

const container = {
  hidden: { opacity: 1 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08, delayChildren: 0.05 },
  },
};

const item = {
  hidden: { opacity: 0, y: 16 },
  show: {
    opacity: 1,
    y: 0,
    transition: { type: "spring" as const, stiffness: 380, damping: 32 },
  },
};

const iconStroke = 1.875;

export function HeroSection() {
  const { startFlow } = useQuiz();

  const scrollQuiz = () => {
    document.getElementById("quiz-calculator")?.scrollIntoView({
      behavior: "smooth",
    });
  };

  return (
    <section
      className="ds-hero-spec relative overflow-hidden border-b border-[color-mix(in_srgb,white_12%,transparent)]"
      aria-labelledby="hero-title"
    >
      <div className="ds-hero-spec-lines" aria-hidden>
        <span />
        <span />
        <span />
      </div>

      <div className="relative mx-auto box-border w-full max-w-6xl px-4 pb-14 pt-12 min-[360px]:px-5 sm:px-6 lg:grid lg:grid-cols-[minmax(0,1.08fr)_minmax(0,0.92fr)] lg:items-center lg:gap-16 lg:px-8 lg:pb-28 lg:pt-20">
        <motion.div
          variants={container}
          initial="hidden"
          animate="show"
          className="text-center lg:text-left"
        >
          <motion.p
            variants={item}
            className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/[0.08] px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.2em] text-white/85 backdrop-blur-sm min-[360px]:text-xs"
          >
            <Shield className="h-3.5 w-3.5 text-white/90" strokeWidth={iconStroke} aria-hidden />
            {hero.eyebrow}
          </motion.p>

          <motion.h1
            id="hero-title"
            variants={item}
            className="mt-6 text-balance font-serif font-semibold leading-[1.1] tracking-tight text-white text-[clamp(2.125rem,5.5vw,3.75rem)]"
          >
            {hero.title}
          </motion.h1>

          <motion.p
            variants={item}
            className="mx-auto mt-6 max-w-xl text-pretty text-base leading-relaxed text-white/80 md:text-lg lg:mx-0 lg:max-w-[38rem]"
          >
            {hero.subtitle}
          </motion.p>

          <motion.ul
            variants={item}
            className="mx-auto mt-8 max-w-xl space-y-3 text-left lg:mx-0"
            aria-label="Ключевые возможности"
          >
            {hero.bullets.map((b) => (
              <li key={b} className="flex gap-3 text-[0.9375rem] leading-snug text-white/90 md:text-base">
                <CheckCircle2
                  className="mt-0.5 h-5 w-5 shrink-0 text-white/75"
                  strokeWidth={iconStroke}
                  aria-hidden
                />
                <span>{b}</span>
              </li>
            ))}
          </motion.ul>

          <motion.div
            variants={item}
            className="mt-10 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:justify-center lg:justify-start"
          >
            <Button
              variant="cta"
              size="lg"
              className="w-full sm:w-auto sm:min-w-[240px]"
              onClick={() => {
                startFlow("fresh");
                scrollQuiz();
              }}
            >
              {hero.ctaPrimary}
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="w-full border-2 border-white/85 bg-transparent text-white shadow-none hover:bg-white/10 hover:text-white sm:w-auto sm:min-w-[220px]"
              onClick={() => {
                startFlow("clarify");
                scrollQuiz();
              }}
            >
              {hero.ctaDelay}
            </Button>
          </motion.div>

          <motion.p
            variants={item}
            className="mx-auto mt-4 max-w-xl text-center text-sm leading-relaxed text-white/65 lg:mx-0 lg:text-left"
          >
            {hero.ctaHint}
          </motion.p>

          <motion.p
            variants={item}
            className="mx-auto mt-3 text-center text-xs font-medium text-white/55 lg:mx-0 lg:text-left"
          >
            {hero.trustLine.join(" · ")}
          </motion.p>

          <motion.button
            variants={item}
            type="button"
            onClick={scrollQuiz}
            className="mx-auto mt-8 flex items-center gap-2 rounded-lg text-sm font-medium text-white/90 transition-colors hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/35 focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--primary-navy)] lg:mx-0"
          >
            <ArrowDown className="h-4 w-4 motion-safe:animate-bounce" strokeWidth={iconStroke} aria-hidden />
            {hero.scrollToQuiz}
          </motion.button>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, type: "spring", stiffness: 300, damping: 28 }}
          className="mt-14 lg:mt-0"
        >
          <div className="ds-spec-card ds-spec-card-hover mx-auto max-w-md lg:max-w-none">
            <p className="border-b border-[var(--light-blue-divider)] pb-3 text-xs font-semibold uppercase tracking-[0.18em] text-[var(--text-secondary)]">
              {hero.summaryCardTitle}
            </p>
            <ul className="mt-5 space-y-4">
              {hero.summaryPayoutLines.map((line) => (
                <li
                  key={line}
                  className="flex gap-3 text-sm leading-snug text-[var(--text-primary)] md:text-[0.9375rem]"
                >
                  <span
                    className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--deep-blue)]"
                    aria-hidden
                  />
                  <span>{line}</span>
                </li>
              ))}
            </ul>
            <p className="mt-6 border-t border-[var(--light-blue-divider)] pt-4 text-sm leading-relaxed text-[var(--text-secondary)]">
              {hero.summaryRegionalNote}
            </p>
            <p className="mt-3 text-sm leading-relaxed text-[var(--text-secondary)]">
              {hero.summarySubmittedNote}
            </p>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
