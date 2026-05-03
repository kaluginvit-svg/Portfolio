"use client";

import dynamic from "next/dynamic";
import { quizSection } from "@/data/texts/landing";

function QuizSectionLoading() {
  return (
    <section
      id="quiz-calculator"
      aria-labelledby="quiz-heading-loading"
      aria-busy="true"
      role="status"
      className="ds-section-y scroll-mt-[4.5rem] border-b border-[var(--cool-border)] bg-[var(--section-bg)] px-4 min-[360px]:px-5 lg:px-8"
    >
      <span id="quiz-heading-loading" className="sr-only">
        Загрузка раздела: {quizSection.title}
      </span>
      <div className="mx-auto max-w-[860px]">
        <div
          className="ds-quiz-card mx-auto min-h-[280px] space-y-5 p-6 animate-pulse md:p-8"
          aria-hidden
        >
          <div className="h-10 rounded-xl bg-[color-mix(in_srgb,var(--section-bg)_92%,var(--cool-border))]" />
          <div className="h-2 w-full max-w-md rounded-full bg-[color-mix(in_srgb,var(--section-bg)_92%,var(--cool-border))]" />
          <div className="space-y-3 rounded-xl border border-[var(--light-blue-divider)] bg-[var(--neutral-surface)] p-5">
            <div className="h-4 w-40 rounded bg-[var(--section-bg)]" />
            <div className="h-14 rounded-xl bg-white" />
            <div className="h-14 rounded-xl bg-white" />
          </div>
        </div>
      </div>
    </section>
  );
}

const QuizSectionContent = dynamic(
  () =>
    import("@/components/sections/quiz-section").then((mod) => mod.QuizSection),
  { loading: () => <QuizSectionLoading />, ssr: true },
);

/** Тяжёлая секция (Framer Motion + квиз) подгружается отдельным чанком после первого кадра. */
export function QuizSectionDynamic() {
  return <QuizSectionContent />;
}
