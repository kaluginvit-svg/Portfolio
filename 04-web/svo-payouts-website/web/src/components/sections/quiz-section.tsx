"use client";

import { motion } from "framer-motion";
import { Calculator } from "lucide-react";
import { QuizFlow } from "@/components/quiz/QuizFlow";
import { quizSection } from "@/data/texts/landing";

const stroke = 1.875;

export function QuizSection() {
  return (
    <section
      id="quiz-calculator"
      className="ds-section-y scroll-mt-[4.5rem] border-b border-[var(--cool-border)] bg-[var(--section-bg)] px-4 min-[360px]:px-5 lg:px-8"
      aria-labelledby="quiz-heading"
    >
      <div className="mx-auto max-w-6xl">
        <div className="mx-auto max-w-2xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-40px" }}
            transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
            className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-[var(--cool-border)] bg-white text-[var(--deep-blue)] shadow-[var(--shadow-spec-card)]"
          >
            <Calculator className="h-7 w-7" strokeWidth={stroke} aria-hidden />
          </motion.div>
          <motion.p
            initial={{ opacity: 0, y: 8 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-40px" }}
            transition={{ delay: 0.04, duration: 0.4 }}
            className="ds-section-kicker mt-6"
          >
            {quizSection.kicker}
          </motion.p>
          <motion.h2
            id="quiz-heading"
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-40px" }}
            transition={{ delay: 0.06, duration: 0.45 }}
            className="ds-h2 mt-3 text-balance text-[var(--deep-blue)]"
          >
            {quizSection.title}
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 8 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-40px" }}
            transition={{ delay: 0.1, duration: 0.4 }}
            className="ds-body mt-5 text-pretty text-[var(--text-secondary)]"
          >
            {quizSection.subtitle}
          </motion.p>
        </div>
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-30px" }}
          transition={{ delay: 0.12, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="mt-12 md:mt-16 lg:mt-20"
        >
          <QuizFlow />
        </motion.div>
      </div>
    </section>
  );
}
