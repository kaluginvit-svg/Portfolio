"use client";

import { motion } from "framer-motion";
import { HelpCircle } from "lucide-react";
import { faqItems, faqSection } from "@/data/texts/landing";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Card, CardContent } from "@/components/ui/card";

const stroke = 1.875;

export function FaqSection() {
  return (
    <section
      id="faq"
      aria-labelledby="faq-heading"
      className="ds-section-y scroll-mt-[4.5rem] border-b border-[var(--cool-border)] bg-[var(--section-bg)] px-4 min-[360px]:px-5 lg:px-8"
    >
      <div className="mx-auto max-w-3xl">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
          className="flex flex-col items-center text-center"
        >
          <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-[var(--cool-border)] bg-white text-[var(--deep-blue)] shadow-[var(--shadow-spec-card)]">
            <HelpCircle className="h-6 w-6" strokeWidth={stroke} aria-hidden />
          </div>
          <p className="ds-section-kicker mt-6">{faqSection.kicker}</p>
          <h2 id="faq-heading" className="ds-h2 mt-2 text-[var(--deep-blue)]">
            {faqSection.title}
          </h2>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.06, duration: 0.45 }}
          className="mt-10"
        >
          <Card className="overflow-hidden rounded-3xl border border-[var(--light-blue-divider)] shadow-[var(--shadow-spec-quiz)]">
            <CardContent className="p-0">
              <Accordion type="single" collapsible className="w-full px-1">
                {faqItems.map((item, i) => (
                  <AccordionItem
                    key={item.q}
                    value={`item-${i}`}
                    className="border-[var(--light-blue-divider)] px-4 sm:px-5"
                  >
                    <AccordionTrigger className="py-5 text-left text-base font-medium text-[var(--text-primary)] hover:no-underline md:text-[1.05rem]">
                      {item.q}
                    </AccordionTrigger>
                    <AccordionContent className="pb-5 text-[0.9375rem] leading-relaxed text-[var(--text-secondary)]">
                      {item.a}
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </section>
  );
}
