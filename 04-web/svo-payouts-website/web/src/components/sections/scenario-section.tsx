"use client";

import { motion } from "framer-motion";
import { ArrowRight, FilePlus2, Timer, type LucideIcon } from "lucide-react";
import { scenarios } from "@/data/texts/landing";
import { useQuiz } from "@/contexts/quiz-context";
import type { FlowMode } from "@/types/quiz";
import { cn } from "@/lib/utils";

const stroke = 1.875;

export function ScenarioSection() {
  const { state, startFlow } = useQuiz();

  const scrollQuiz = () => {
    document.getElementById("quiz-calculator")?.scrollIntoView({
      behavior: "smooth",
    });
  };

  const pick = (mode: FlowMode) => {
    startFlow(mode);
    scrollQuiz();
  };

  return (
    <section
      id="scenarios"
      aria-labelledby="scenarios-heading"
      className="ds-section-y scroll-mt-[4.5rem] border-b border-[var(--cool-border)] bg-[var(--section-bg)] px-4 min-[360px]:px-5 lg:px-8"
    >
      <div className="mx-auto max-w-5xl">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
          className="text-center"
        >
          <p className="ds-section-kicker">{scenarios.kicker}</p>
          <h2 id="scenarios-heading" className="ds-h2 mt-3">
            {scenarios.title}
          </h2>
        </motion.div>
        <div className="mt-12 grid gap-5 md:grid-cols-2 md:gap-6 lg:mt-16 lg:gap-8">
          <ScenarioCard
            icon={FilePlus2}
            title={scenarios.a.title}
            description={scenarios.a.description}
            ctaLabel={scenarios.a.cta}
            selected={state.flowMode === "fresh"}
            onClick={() => pick("fresh")}
            variant="federal"
          />
          <ScenarioCard
            icon={Timer}
            title={scenarios.b.title}
            description={scenarios.b.description}
            ctaLabel={scenarios.b.cta}
            selected={state.flowMode === "clarify"}
            onClick={() => pick("clarify")}
            variant="diagnostic"
          />
        </div>
      </div>
    </section>
  );
}

function ScenarioCard({
  icon: Icon,
  title,
  description,
  ctaLabel,
  selected,
  onClick,
  variant,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  ctaLabel: string;
  selected: boolean;
  onClick: () => void;
  variant: "federal" | "diagnostic";
}) {
  return (
    <motion.button
      type="button"
      whileHover={{ y: -2 }}
      whileTap={{ scale: 0.992 }}
      transition={{ type: "spring", stiffness: 400, damping: 26 }}
      onClick={onClick}
      aria-pressed={selected}
      className={cn(
        "group relative flex h-full flex-col overflow-hidden rounded-[20px] border bg-white p-6 text-left shadow-[var(--shadow-spec-card)] transition-[border-color,box-shadow] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--deep-blue)_30%,transparent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--section-bg)] md:p-8",
        variant === "federal" &&
          "before:pointer-events-none before:absolute before:inset-x-0 before:top-0 before:h-1 before:rounded-t-[20px] before:bg-[#163A63]",
        variant === "diagnostic" &&
          "before:pointer-events-none before:absolute before:inset-x-0 before:top-0 before:h-1 before:rounded-t-[20px] before:bg-[#2563EB]",
        selected
          ? "border-[var(--deep-blue)] shadow-[0_0_0_3px_rgba(22,58,99,0.1),var(--shadow-spec-card)]"
          : "border-[var(--cool-border)] hover:border-[color-mix(in_srgb,var(--deep-blue)_35%,var(--cool-border))] hover:shadow-[0_14px_36px_rgba(11,31,58,0.1)]",
      )}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--soft-blue-bg)] text-[var(--deep-blue)]">
        <Icon className="h-6 w-6" strokeWidth={stroke} aria-hidden />
      </div>
      <span className="mt-5 font-serif text-xl font-semibold leading-tight text-[var(--text-primary)] md:text-2xl">
        {title}
      </span>
      <p className="mt-3 flex-1 text-sm leading-relaxed text-[var(--text-secondary)] md:text-base">
        {description}
      </p>
      <span className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-[var(--deep-blue)]">
        {ctaLabel}
        <ArrowRight
          className="h-4 w-4 transition-transform group-hover:translate-x-0.5"
          strokeWidth={stroke}
          aria-hidden
        />
      </span>
    </motion.button>
  );
}
