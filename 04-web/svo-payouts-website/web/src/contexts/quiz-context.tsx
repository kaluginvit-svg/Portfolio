"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { trackEvent } from "@/lib/analytics/track";
import type { FlowMode, QuizAnswers, QuizPersistedState } from "@/types/quiz";
import { preserveClarifyAnswersForFreshFlow } from "@/lib/quiz/preserve-clarify-for-fresh";
import {
  clearQuizState,
  defaultQuizState,
  loadQuizState,
  saveQuizState,
} from "@/lib/storage/quiz-storage";

type QuizContextValue = {
  state: QuizPersistedState;
  hydrated: boolean;
  startFlow: (mode: FlowMode) => void;
  /** После завершённого clarify: начать полный расчёт, сохранив ответы опроса про документы. */
  startFreshAfterClarify: () => void;
  setAnswers: (patch: Partial<QuizAnswers>) => void;
  setStepIndex: (index: number) => void;
  complete: () => void;
  reset: () => void;
};

const QuizContext = createContext<QuizContextValue | null>(null);

export function QuizProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<QuizPersistedState>(defaultQuizState);
  const [hydrated, setHydrated] = useState(false);
  const stateRef = useRef(state);
  stateRef.current = state;

  useEffect(() => {
    const saved = loadQuizState();
    if (saved) setState(saved);
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    saveQuizState(state);
  }, [state, hydrated]);

  const startFlow = useCallback((mode: FlowMode) => {
    if (mode === "fresh") {
      trackEvent("fresh_flow_selected", { flow_mode: "fresh" });
    } else {
      trackEvent("stuck_flow_selected", { flow_mode: "clarify" });
    }
    trackEvent("quiz_start", { flow_mode: mode });
    setState({
      version: 5,
      flowMode: mode,
      stepIndex: 0,
      answers: {},
      completed: false,
    });
  }, []);

  const startFreshAfterClarify = useCallback(() => {
    trackEvent("quiz_clarify_to_fresh", {});
    trackEvent("quiz_start", { flow_mode: "fresh" });
    setState((prev) => ({
      version: 5,
      flowMode: "fresh",
      stepIndex: 0,
      answers: preserveClarifyAnswersForFreshFlow(prev.answers),
      completed: false,
    }));
  }, []);

  const setAnswers = useCallback((patch: Partial<QuizAnswers>) => {
    setState((prev) => ({
      ...prev,
      answers: { ...prev.answers, ...patch },
    }));
  }, []);

  const setStepIndex = useCallback((index: number) => {
    setState((prev) => ({ ...prev, stepIndex: index }));
  }, []);

  const complete = useCallback(() => {
    const mode = stateRef.current.flowMode;
    trackEvent("quiz_complete", {
      flow_mode: mode ?? "unknown",
    });
    setState((prev) => ({ ...prev, completed: true }));
  }, []);

  const reset = useCallback(() => {
    clearQuizState();
    setState(defaultQuizState());
  }, []);

  const value = useMemo(
    () => ({
      state,
      hydrated,
      startFlow,
      startFreshAfterClarify,
      setAnswers,
      setStepIndex,
      complete,
      reset,
    }),
    [
      state,
      hydrated,
      startFlow,
      startFreshAfterClarify,
      setAnswers,
      setStepIndex,
      complete,
      reset,
    ],
  );

  return <QuizContext.Provider value={value}>{children}</QuizContext.Provider>;
}

export function useQuiz() {
  const ctx = useContext(QuizContext);
  if (!ctx) throw new Error("useQuiz must be used within QuizProvider");
  return ctx;
}
