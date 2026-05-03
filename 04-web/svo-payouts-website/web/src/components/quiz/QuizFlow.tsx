"use client";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useQuiz } from "@/contexts/quiz-context";
import { clampStepIndex, getVisibleSteps, isClarifyStep, isFreshPayStep } from "@/lib/quiz/steps";
import { validateQuizStep } from "@/lib/quiz/validate-quiz-step";
import type { QuizAnswers, QuizStepId } from "@/types/quiz";
import { quizFlowCopy, stepQuestions } from "@/data/texts/quiz-copy";
import {
  ambiguityFlagOptions,
  calcModeOptions,
  deathBasisOptions,
  freshApplicantRoleOptions,
  freshChildrenCountOptions,
  freshRecipientsCountOptions,
  freshStepQuestions,
  serviceStatusOptions,
} from "@/data/texts/fresh-quiz-copy";
import {
  clarifyCopiesOptions,
  clarifyDeathCertOptions,
  clarifyFilingOptions,
  clarifyGoalPrimaryOptions,
  clarifyGoalSecondaryOptions,
  clarifyKinshipOptions,
  clarifyMilitaryNoticeOptions,
  clarifyPostFilingFeedbackOptions,
  clarifyQuizCopy,
  clarifyStage1Options,
  clarifyStepHints,
  clarifyStepQuestions,
  clarifyWhereSubmittedOnlyOptions,
} from "@/data/texts/clarify-quiz-copy";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { ClarifyThankYou } from "@/components/quiz/ClarifyThankYou";
import { QuizResult } from "@/components/quiz/QuizResult";
import { cn } from "@/lib/utils";

/** Шаги полного расчёта, где нужен явный «Далее» (свободный ввод региона). */
function freshStepNeedsNextButton(id: QuizStepId | undefined): boolean {
  return id === "region";
}

function QuizFlowSkeleton() {
  return (
    <div
      className="ds-quiz-card mx-auto space-y-5 p-6 animate-pulse md:p-8"
      aria-busy="true"
      aria-label="Загрузка расчёта"
    >
      <div className="h-10 rounded-xl bg-[var(--section-bg)]" />
      <div className="ds-quiz-progress-track bg-[var(--section-bg)]" />
      <div className="space-y-3 rounded-xl border border-[var(--light-blue-divider)] bg-[var(--neutral-surface)] p-5">
        <div className="h-4 w-40 rounded bg-[var(--section-bg)]" />
        <div className="h-14 rounded-xl bg-white" />
        <div className="h-14 rounded-xl bg-white" />
      </div>
    </div>
  );
}

export function QuizFlow() {
  const {
    state,
    hydrated,
    startFlow,
    startFreshAfterClarify,
    setAnswers,
    setStepIndex,
    complete,
    reset,
  } = useQuiz();
  const [error, setError] = useState<string | null>(null);
  const reducedMotion = useReducedMotion();

  const stepMotion = useMemo(
    () =>
      reducedMotion
        ? {
            initial: { opacity: 0 },
            animate: { opacity: 1, transition: { duration: 0.18 } },
            exit: { opacity: 0, transition: { duration: 0.12 } },
          }
        : {
            initial: { opacity: 0, x: 14 },
            animate: {
              opacity: 1,
              x: 0,
              transition: {
                type: "spring" as const,
                stiffness: 400,
                damping: 34,
                mass: 0.72,
              },
            },
            exit: {
              opacity: 0,
              x: -10,
              transition: { duration: 0.2, ease: "easeIn" as const },
            },
          },
    [reducedMotion],
  );

  const flowMode = state.flowMode;
  const answers = state.answers;

  const steps = useMemo(() => {
    if (!flowMode) return [] as QuizStepId[];
    return getVisibleSteps(flowMode, answers);
  }, [flowMode, answers]);

  const safeIndex = clampStepIndex(state.stepIndex, steps.length);
  const currentId = steps[safeIndex];
  const progress =
    steps.length > 0 ? Math.round(((safeIndex + 1) / steps.length) * 100) : 0;

  useEffect(() => {
    if (!flowMode || state.completed) return;
    const max = Math.max(0, steps.length - 1);
    if (state.stepIndex > max) setStepIndex(max);
  }, [flowMode, state.completed, state.stepIndex, steps.length, setStepIndex]);

  const pickClarify = useCallback(
    (patch: Partial<QuizAnswers>) => {
      if (flowMode !== "clarify") return;
      setError(null);
      const mergedPatch: Partial<QuizAnswers> = { ...patch };
      if (patch.clarifyFilingStatus === "not_yet") {
        mergedPatch.clarifyWhereSubmitted = undefined;
        mergedPatch.clarifyPostFilingFeedback = undefined;
      }
      const nextAnswers = { ...answers, ...mergedPatch };
      const err = validateQuizStep(currentId, nextAnswers);
      if (err) {
        setError(err);
        return;
      }
      setAnswers(mergedPatch);
      if (safeIndex >= steps.length - 1) {
        complete();
      } else {
        setStepIndex(safeIndex + 1);
      }
    },
    [
      flowMode,
      answers,
      currentId,
      safeIndex,
      steps.length,
      setAnswers,
      setStepIndex,
      complete,
    ],
  );

  const pickFresh = useCallback(
    (patch: Partial<QuizAnswers>) => {
      if (flowMode !== "fresh") return;
      setError(null);
      const nextAnswers = { ...answers, ...patch };
      const err = validateQuizStep(currentId, nextAnswers);
      if (err) {
        setError(err);
        return;
      }
      setAnswers(patch);
      if (safeIndex >= steps.length - 1) {
        complete();
      } else {
        setStepIndex(safeIndex + 1);
      }
    },
    [
      flowMode,
      answers,
      currentId,
      safeIndex,
      steps.length,
      setAnswers,
      setStepIndex,
      complete,
    ],
  );

  if (!hydrated) {
    return <QuizFlowSkeleton />;
  }

  const goNext = () => {
    const err = validateQuizStep(currentId, answers);
    if (err) {
      setError(err);
      return;
    }
    setError(null);
    if (!flowMode) return;
    if (safeIndex >= steps.length - 1) {
      complete();
      return;
    }
    setStepIndex(safeIndex + 1);
  };

  const goBack = () => {
    setError(null);
    if (safeIndex <= 0) return;
    setStepIndex(safeIndex - 1);
  };

  const scrollToLead = () => {
    const section = document.getElementById("lead-form");
    section?.scrollIntoView({ behavior: "smooth", block: "start" });
    window.setTimeout(() => {
      document.getElementById("lead-name")?.focus();
    }, 450);
  };

  if (!flowMode) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
        className="mx-auto w-full max-w-[860px]"
      >
        <div className="ds-quiz-card overflow-hidden">
          <div className="border-b border-[var(--light-blue-divider)] bg-[var(--neutral-surface)] px-6 py-6 md:px-10 md:py-8">
            <div
              className="h-1 w-16 rounded-full bg-gradient-to-r from-[#163A63] to-[#B3262E]"
              aria-hidden
            />
            <h2 className="mt-5 font-serif text-xl font-semibold leading-snug text-[var(--text-primary)] md:text-2xl">
              {quizFlowCopy.emptyTitle}
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-[var(--text-secondary)] md:text-base">
              {quizFlowCopy.emptySubtitle}
            </p>
          </div>
          <div className="flex flex-col gap-3 p-6 md:flex-row md:flex-wrap md:gap-4 md:p-10">
            <Button variant="cta" size="touch" className="md:flex-1" onClick={() => startFlow("fresh")}>
              {quizFlowCopy.btnScenarioA}
            </Button>
            <Button variant="outline" size="touch" className="md:flex-1" onClick={() => startFlow("clarify")}>
              {quizFlowCopy.btnScenarioB}
            </Button>
          </div>
        </div>
      </motion.div>
    );
  }

  if (state.completed && flowMode === "clarify") {
    return (
      <ClarifyThankYou
        onLead={scrollToLead}
        onStartCalculator={() => {
          startFreshAfterClarify();
          document.getElementById("quiz-calculator")?.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
        }}
        onAgain={() => {
          reset();
          startFlow("clarify");
        }}
      />
    );
  }

  if (state.completed && flowMode === "fresh") {
    return (
      <QuizResult
        answers={answers}
        onAgain={() => {
          reset();
          startFlow("fresh");
        }}
        onLead={scrollToLead}
        onPersonalBreakdown={scrollToLead}
      />
    );
  }

  const titleForStep =
    currentId && clarifyStepQuestions[currentId]
      ? clarifyStepQuestions[currentId]
      : currentId && freshStepQuestions[currentId]
        ? freshStepQuestions[currentId]
        : currentId
          ? stepQuestions[currentId] ?? ""
          : "";

  const clarifyHint = currentId ? clarifyStepHints[currentId] : undefined;

  return (
    <div className="mx-auto w-full max-w-[860px] space-y-0">
      <div className="ds-quiz-card overflow-hidden">
        <div className="border-b border-[var(--light-blue-divider)] bg-[var(--neutral-surface)] px-6 py-5 md:px-10 md:py-6">
          <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-[var(--text-secondary)] sm:text-sm">
            <p>
              <span className="sr-only">Режим: </span>
              <span className="font-semibold text-[var(--deep-blue)]">
                {flowMode === "fresh" ? quizFlowCopy.badgeFresh : quizFlowCopy.badgeClarify}
              </span>
              {flowMode === "clarify" && currentId && isClarifyStep(currentId) ? (
                <span className="text-[var(--text-secondary)]"> · {quizFlowCopy.clarifyProgressHint}</span>
              ) : null}
            </p>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-9 min-h-9 -mr-1 text-xs font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              onClick={() => {
                if (typeof window !== "undefined" && !window.confirm(quizFlowCopy.resetConfirm)) {
                  return;
                }
                reset();
              }}
            >
              {quizFlowCopy.resetQuiz}
            </Button>
          </div>
          <div className="mt-4 space-y-3">
            <div className="flex items-baseline justify-between gap-3 text-sm">
              <span id="quiz-progress-label" className="font-semibold text-[var(--deep-blue)]">
                {quizFlowCopy.progressQuestion(safeIndex + 1, steps.length)}
              </span>
              <span className="tabular-nums text-[var(--text-secondary)]" aria-hidden>
                {progress}%
              </span>
            </div>
            <Progress
              value={progress}
              aria-labelledby="quiz-progress-label"
              getValueLabel={(value) =>
                `Шаг ${safeIndex + 1} из ${steps.length}, ${Math.round(value ?? 0)} процентов`
              }
            />
          </div>
        </div>

        <div className="border-b border-[var(--light-blue-divider)] bg-white px-6 py-6 md:px-10 md:py-8">
          <h3 className="font-serif text-lg font-semibold leading-snug text-pretty text-[var(--text-primary)] md:text-xl">
            {titleForStep}
          </h3>
          {clarifyHint ? (
            <p className="mt-3 text-sm leading-relaxed text-[var(--text-secondary)] md:text-[0.9375rem]">
              {clarifyHint}
            </p>
          ) : null}
          {flowMode === "clarify" && currentId && isClarifyStep(currentId) ? (
            <p className="mt-2 text-xs leading-relaxed text-[var(--text-secondary)] sm:text-sm">
              {clarifyQuizCopy.tapToContinue}
            </p>
          ) : null}
          {flowMode === "fresh" && currentId && isFreshPayStep(currentId) && currentId !== "region" ? (
            <p className="mt-2 text-xs leading-relaxed text-[var(--text-secondary)] sm:text-sm">
              {quizFlowCopy.tapToContinueFresh}
            </p>
          ) : null}
        </div>

        <div className="space-y-8 bg-white px-6 py-8 md:px-10 md:py-10">
          <AnimatePresence mode="wait">
            {currentId ? (
              <motion.div key={currentId} {...stepMotion} className="min-h-[120px]">
                <StepBody
                  id={currentId}
                  answers={answers}
                  setAnswers={setAnswers}
                  onClarifyPick={flowMode === "clarify" ? pickClarify : undefined}
                  onFreshPick={flowMode === "fresh" ? pickFresh : undefined}
                />
              </motion.div>
            ) : null}
          </AnimatePresence>

          {error ? (
            <p
              className="rounded-xl border border-[color-mix(in_srgb,var(--accent-red)_35%,var(--cool-border))] bg-[var(--soft-red-bg)] px-3.5 py-2.5 text-sm text-[var(--status-alert)]"
              role="alert"
              aria-live="polite"
            >
              {error}
            </p>
          ) : null}

          <div
            className={cn(
              "flex flex-col-reverse gap-3 pt-1 sm:flex-row sm:gap-4",
              flowMode === "fresh" && freshStepNeedsNextButton(currentId)
                ? "sm:justify-between"
                : "sm:justify-start",
            )}
          >
            <Button
              type="button"
              variant="outline"
              size="touch"
              className="sm:w-auto sm:min-w-[8rem] sm:px-6"
              onClick={goBack}
              disabled={safeIndex <= 0}
            >
              {quizFlowCopy.back}
            </Button>
            {flowMode === "fresh" && freshStepNeedsNextButton(currentId) ? (
              <Button
                type="button"
                variant="cta"
                size="touch"
                className="sm:w-auto sm:min-w-[10rem] sm:px-8"
                onClick={goNext}
              >
                {safeIndex >= steps.length - 1 ? quizFlowCopy.showResult : quizFlowCopy.next}
              </Button>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}

function StepBody({
  id,
  answers,
  setAnswers,
  onClarifyPick,
  onFreshPick,
}: {
  id: QuizStepId;
  answers: QuizAnswers;
  setAnswers: (p: Partial<QuizAnswers>) => void;
  onClarifyPick?: (patch: Partial<QuizAnswers>) => void;
  onFreshPick?: (patch: Partial<QuizAnswers>) => void;
}) {
  const pick = onClarifyPick ?? ((p: Partial<QuizAnswers>) => setAnswers(p));
  const fresh = onFreshPick ?? ((p: Partial<QuizAnswers>) => setAnswers(p));

  if (id === "clarify_stage_1") {
    return (
      <div className="grid gap-3 sm:gap-3" role="listbox" aria-label="Ваша ситуация">
        {clarifyStage1Options.map((o) => (
          <OptionRow
            key={o.id}
            selected={answers.clarifyStage1 === o.id}
            onClick={() => pick({ clarifyStage1: o.id })}
          >
            {o.label}
          </OptionRow>
        ))}
      </div>
    );
  }

  if (id === "clarify_doc_1") {
    return (
      <div className="grid gap-3 sm:gap-3" role="listbox" aria-label="Свидетельство о смерти">
        {clarifyDeathCertOptions.map((o) => (
          <OptionRow
            key={o.id}
            selected={answers.clarifyDeathCert === o.id}
            onClick={() => pick({ clarifyDeathCert: o.id })}
          >
            {o.label}
          </OptionRow>
        ))}
      </div>
    );
  }

  if (id === "clarify_doc_2") {
    return (
      <div className="grid gap-3 sm:gap-3" role="listbox" aria-label="Документы из части">
        {clarifyMilitaryNoticeOptions.map((o) => (
          <OptionRow
            key={o.id}
            selected={answers.clarifyMilitaryNotice === o.id}
            onClick={() => pick({ clarifyMilitaryNotice: o.id })}
          >
            {o.label}
          </OptionRow>
        ))}
      </div>
    );
  }

  if (id === "clarify_doc_3") {
    return (
      <div className="grid gap-3 sm:gap-3" role="listbox" aria-label="Родство">
        {clarifyKinshipOptions.map((o) => (
          <OptionRow
            key={o.id}
            selected={answers.clarifyKinshipDocs === o.id}
            onClick={() => pick({ clarifyKinshipDocs: o.id })}
          >
            {o.label}
          </OptionRow>
        ))}
      </div>
    );
  }

  if (id === "clarify_doc_4") {
    return (
      <div className="grid gap-3 sm:gap-3" role="listbox" aria-label="Готовность пакета для подачи">
        {clarifyCopiesOptions.map((o) => (
          <OptionRow
            key={o.id}
            selected={answers.clarifyCopiesStatus === o.id}
            onClick={() => pick({ clarifyCopiesStatus: o.id })}
          >
            {o.label}
          </OptionRow>
        ))}
      </div>
    );
  }

  if (id === "clarify_doc_5") {
    return (
      <div className="grid gap-3 sm:gap-3" role="listbox" aria-label="Подача документов">
        {clarifyFilingOptions.map((o) => (
          <OptionRow
            key={o.id}
            selected={answers.clarifyFilingStatus === o.id}
            onClick={() => pick({ clarifyFilingStatus: o.id })}
            description={o.hint}
          >
            {o.label}
          </OptionRow>
        ))}
      </div>
    );
  }

  if (id === "clarify_doc_6") {
    return (
      <div className="grid gap-3 sm:gap-3" role="listbox" aria-label="Куда подавали документы">
        {clarifyWhereSubmittedOnlyOptions.map((o) => (
          <OptionRow
            key={o.id}
            selected={answers.clarifyWhereSubmitted === o.id}
            onClick={() => pick({ clarifyWhereSubmitted: o.id })}
          >
            {o.label}
          </OptionRow>
        ))}
      </div>
    );
  }

  if (id === "clarify_feedback_1") {
    return (
      <div className="grid gap-3 sm:gap-3" role="listbox" aria-label="Ситуация после подачи">
        {clarifyPostFilingFeedbackOptions.map((o) => (
          <OptionRow
            key={o.id}
            selected={answers.clarifyPostFilingFeedback === o.id}
            onClick={() => pick({ clarifyPostFilingFeedback: o.id })}
            description={o.hint}
          >
            {o.label}
          </OptionRow>
        ))}
      </div>
    );
  }

  if (id === "clarify_goal_1") {
    return (
      <div className="grid gap-3 sm:gap-3" role="listbox" aria-label="Что мешает">
        {clarifyGoalPrimaryOptions.map((o) => (
          <OptionRow
            key={o.id}
            selected={answers.clarifyGoalPrimary === o.id}
            onClick={() => pick({ clarifyGoalPrimary: o.id })}
          >
            {o.label}
          </OptionRow>
        ))}
      </div>
    );
  }

  if (id === "clarify_goal_2") {
    return (
      <div className="grid gap-3 sm:gap-3" role="listbox" aria-label="Что нужнее всего">
        {clarifyGoalSecondaryOptions.map((o) => (
          <OptionRow
            key={o.id}
            selected={answers.clarifyGoalSecondary === o.id}
            onClick={() => pick({ clarifyGoalSecondary: o.id })}
          >
            {o.label}
          </OptionRow>
        ))}
      </div>
    );
  }

  if (id === "service_status") {
    return (
      <div className="grid gap-3 sm:gap-3" role="listbox" aria-label="Категория погибшего">
        {serviceStatusOptions.map((o) => (
          <OptionRow
            key={o.id}
            selected={answers.serviceStatus === o.id}
            onClick={() => fresh({ serviceStatus: o.id })}
          >
            {o.label}
          </OptionRow>
        ))}
      </div>
    );
  }

  if (id === "applicant_role") {
    return (
      <div className="grid gap-3 sm:gap-3" role="listbox" aria-label="Кто вы">
        {freshApplicantRoleOptions.map((o) => (
          <OptionRow
            key={o.id}
            selected={answers.freshApplicantRole === o.id}
            onClick={() => fresh({ freshApplicantRole: o.id })}
          >
            {o.label}
          </OptionRow>
        ))}
      </div>
    );
  }

  if (id === "recipients_count") {
    return (
      <div
        className="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-3"
        role="listbox"
        aria-label="Число получателей разовых выплат"
      >
        {freshRecipientsCountOptions.map((o) => (
          <OptionRow
            key={o.id}
            selected={answers.freshRecipientsCount === o.id}
            onClick={() => fresh({ freshRecipientsCount: o.id })}
            className="justify-center text-center text-base font-medium"
          >
            {o.label}
          </OptionRow>
        ))}
      </div>
    );
  }

  if (id === "children_count") {
    return (
      <div className="grid gap-3 sm:grid-cols-2 sm:gap-3" role="listbox" aria-label="Дети для ежемесячных выплат">
        {freshChildrenCountOptions.map((o) => (
          <OptionRow
            key={o.id}
            selected={answers.freshChildrenCount === o.id}
            onClick={() => fresh({ freshChildrenCount: o.id })}
          >
            {o.label}
          </OptionRow>
        ))}
      </div>
    );
  }

  if (id === "death_basis") {
    return (
      <div className="grid gap-3 sm:gap-3" role="listbox" aria-label="Причина смерти">
        {deathBasisOptions.map((o) => (
          <OptionRow
            key={o.id}
            selected={answers.deathBasis === o.id}
            onClick={() => fresh({ deathBasis: o.id })}
          >
            {o.label}
          </OptionRow>
        ))}
      </div>
    );
  }

  if (id === "ambiguity_flag") {
    return (
      <div className="grid gap-3 sm:gap-3" role="listbox" aria-label="Спор или неясность">
        {ambiguityFlagOptions.map((o) => (
          <OptionRow
            key={o.id}
            selected={answers.ambiguityFlag === o.id}
            onClick={() => fresh({ ambiguityFlag: o.id })}
          >
            {o.label}
          </OptionRow>
        ))}
      </div>
    );
  }

  if (id === "calc_mode") {
    return (
      <div className="grid gap-3 sm:gap-3" role="listbox" aria-label="Тип расчёта">
        {calcModeOptions.map((o) => (
          <OptionRow
            key={o.id}
            selected={answers.calcMode === o.id}
            onClick={() => fresh({ calcMode: o.id })}
          >
            {o.label}
          </OptionRow>
        ))}
      </div>
    );
  }

  if (id === "region") {
    return (
      <div className="space-y-2">
        <Label htmlFor="quiz-region" className="text-sm font-medium text-[var(--text-primary)]">
          {quizFlowCopy.regionLabel}
        </Label>
        <Input
          id="quiz-region"
          name="region"
          placeholder={quizFlowCopy.regionPlaceholder}
          value={answers.region ?? ""}
          onChange={(e) => setAnswers({ region: e.target.value })}
          autoComplete="address-level1"
          aria-describedby="quiz-region-hint"
        />
        <p id="quiz-region-hint" className="text-xs text-[var(--text-secondary)]">
          {quizFlowCopy.regionHint}
        </p>
      </div>
    );
  }

  return null;
}

function OptionRow({
  children,
  description,
  selected,
  onClick,
  className,
}: {
  children: React.ReactNode;
  description?: string;
  selected: boolean;
  onClick: () => void;
  className?: string;
}) {
  return (
    <motion.button
      type="button"
      onClick={onClick}
      whileTap={{ scale: 0.992 }}
      transition={{ type: "spring", stiffness: 520, damping: 28 }}
      className={cn(
        "flex w-full rounded-xl border px-4 text-left text-base leading-snug tracking-tight transition-[border-color,background-color,box-shadow] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--deep-blue)_22%,transparent)] focus-visible:ring-offset-2 focus-visible:ring-offset-white",
        description ? "min-h-[4.5rem] items-start py-4 sm:min-h-[4.75rem]" : "min-h-14 items-center py-3.5",
        selected
          ? "border-[var(--deep-blue)] bg-[var(--soft-blue-bg)] text-[var(--text-primary)] shadow-[0_0_0_3px_rgba(22,58,99,0.08)]"
          : "border-[var(--cool-border)] bg-white text-[var(--text-primary)] hover:bg-[var(--neutral-surface)]",
        className,
      )}
    >
      <span className="block w-full">
        <span className="block font-medium leading-snug text-[var(--text-primary)]">{children}</span>
        {description ? (
          <span className="mt-1.5 block text-sm font-normal leading-relaxed text-[var(--text-secondary)]">
            {description}
          </span>
        ) : null}
      </span>
    </motion.button>
  );
}
