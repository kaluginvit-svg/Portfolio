"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Check, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { thanksPage } from "@/data/texts/landing";

type Props = {
  /** Текст из CONTACT_TEXT на сервере (опционально). */
  contactNote?: string | null;
};

export function ThanksView({ contactNote = null }: Props) {
  return (
    <div className="relative min-h-[85vh] overflow-hidden px-4 py-16 min-[360px]:px-5 md:flex md:items-center md:justify-center md:py-24 lg:px-8">
      <div
        className="pointer-events-none absolute inset-0 opacity-60"
        aria-hidden
        style={{
          backgroundImage:
            "radial-gradient(ellipse 80% 60% at 50% -20%, color-mix(in srgb, var(--deep-blue) 12%, transparent), transparent), radial-gradient(circle at 100% 100%, color-mix(in srgb, var(--soft-blue-bg) 85%, transparent), transparent 45%)",
        }}
      />
      <motion.div
        initial={{ opacity: 1, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        className="relative mx-auto w-full max-w-lg text-center"
      >
        <motion.div
          initial={{ scale: 0.92, opacity: 1 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.12, type: "spring", stiffness: 320, damping: 22 }}
          className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-[var(--deep-blue)] text-white shadow-[var(--shadow-spec-card)]"
        >
          <Check className="h-10 w-10" strokeWidth={2} aria-hidden />
        </motion.div>

        <motion.div
          initial={{ opacity: 1, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25, duration: 0.4 }}
          className="mt-8 inline-flex items-center gap-2 rounded-full border border-[var(--cool-border)] bg-white px-3 py-1 text-xs font-medium uppercase tracking-wider text-[var(--text-secondary)] shadow-sm"
        >
          <Sparkles className="h-3.5 w-3.5 text-[var(--deep-blue)]" strokeWidth={1.875} aria-hidden />
          {thanksPage.badge}
        </motion.div>

        <motion.h1
          initial={{ opacity: 1, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.32, duration: 0.4 }}
          className="mt-5 font-serif text-3xl font-semibold leading-tight tracking-tight text-[var(--text-primary)] min-[360px]:text-[2rem] md:text-4xl"
        >
          {thanksPage.title}
        </motion.h1>

        <motion.p
          initial={{ opacity: 1, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.4 }}
          className="mx-auto mt-5 max-w-md text-pretty text-base leading-relaxed text-[var(--text-secondary)] md:text-lg"
        >
          {thanksPage.body}
        </motion.p>

        {contactNote ? (
          <motion.div
            initial={{ opacity: 1, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.44, duration: 0.4 }}
            className="mx-auto mt-6 max-w-md rounded-2xl border border-[var(--cool-border)] bg-white px-4 py-4 text-left text-sm leading-relaxed text-[var(--text-primary)] shadow-[var(--shadow-spec-card)]"
          >
            <p className="text-xs font-semibold uppercase tracking-wide text-[var(--text-secondary)]">
              {thanksPage.contactFromEnvTitle}
            </p>
            <p className="mt-2 whitespace-pre-wrap text-pretty">{contactNote}</p>
          </motion.div>
        ) : null}

        <motion.div
          initial={{ opacity: 1, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.4 }}
          className="mt-10 flex flex-col items-center gap-3 sm:flex-row sm:justify-center"
        >
          <Button asChild variant="cta" size="lg" className="w-full min-h-12 sm:w-auto sm:min-w-[200px]">
            <Link href="/">{thanksPage.cta}</Link>
          </Button>
        </motion.div>
      </motion.div>
    </div>
  );
}
