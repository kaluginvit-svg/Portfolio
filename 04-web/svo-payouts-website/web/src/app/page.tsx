import { Suspense } from "react";
import { QuizProvider } from "@/contexts/quiz-context";
import { HeroSection } from "@/components/sections/hero-section";
import { IntentNavSection } from "@/components/sections/intent-nav-section";
import {
  DocumentsIntentSection,
  IfNotPaidIntentSection,
  PaymentsIntentSection,
  PayoutStructureIntentSection,
  SubmittedCasesIntentSection,
  WhereToApplyIntentSection,
} from "@/components/sections/intent-guide-sections";
import { ScenarioSection } from "@/components/sections/scenario-section";
import { QuizSectionDynamic } from "@/components/sections/quiz-section-dynamic";
import { LeadFormSection } from "@/components/sections/lead-form-section";
import { FaqSection } from "@/components/sections/faq-section";
import { FooterSection } from "@/components/sections/footer-section";
import { HomeJsonLd } from "@/components/seo/home-json-ld";

function LeadFormFallback() {
  return (
    <div
      className="mx-auto max-w-lg px-4 py-14"
      role="status"
      aria-live="polite"
      aria-label="Загрузка блока с формой"
    >
      <div className="h-96 animate-pulse rounded-2xl bg-muted/60" />
    </div>
  );
}

export default function HomePage() {
  return (
    <>
      <HomeJsonLd />
      <QuizProvider>
        <main id="main-content" className="w-full min-w-0">
          <HeroSection />
          <IntentNavSection />
          <PaymentsIntentSection />
          <PayoutStructureIntentSection />
          <WhereToApplyIntentSection />
          <IfNotPaidIntentSection />
          <SubmittedCasesIntentSection />
          <DocumentsIntentSection />
          <ScenarioSection />
          <QuizSectionDynamic />
          <Suspense fallback={<LeadFormFallback />}>
            <LeadFormSection />
          </Suspense>
          <FaqSection />
          <FooterSection />
        </main>
      </QuizProvider>
    </>
  );
}
