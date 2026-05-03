import { isLegacyClarifyQuizComplete } from "@/lib/quiz/clarify-complete";
import type { FlowMode, QuizAnswers, QuizPersistedState } from "@/types/quiz";

/** Незавершённый старый fresh-квиз (до 8 шагов): индекс шага больше не совпадает с новой схемой. */
function migrateInProgressLegacyFreshQuiz(
  flowMode: FlowMode | null,
  completed: boolean,
  stepIndex: number,
  answers: QuizAnswers,
): { stepIndex: number; answers: QuizAnswers } {
  if (flowMode !== "fresh" || completed) return { stepIndex, answers };
  if (answers.serviceStatus != null) return { stepIndex, answers };
  if (answers.deceasedRole == null) return { stepIndex, answers };

  const next: QuizAnswers = { ...answers };
  delete next.deceasedRole;
  delete next.relation;
  delete next.relationComplexSub;
  delete next.recipients;
  delete next.recipientsExact;
  delete next.documents;
  return { stepIndex: 0, answers: next };
}

const STORAGE_KEY = "svo_quiz_v2";
const LEGACY_KEY = "svo_quiz_v1";

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

/** Миграция v2 → v5: сценарий B больше не ведёт в расчёт — чистый опрос про документы. */
function migrateV2ToV5(raw: Record<string, unknown>): QuizPersistedState | null {
  const scenario = raw.scenario;
  if (scenario !== "A" && scenario !== "B" && scenario !== null) return null;

  if (scenario === "B") {
    return {
      version: 5,
      flowMode: "clarify",
      stepIndex: 0,
      answers: {},
      completed: false,
    };
  }

  const answers = (isRecord(raw.answers) ? raw.answers : {}) as QuizAnswers;
  const stepIndex =
    typeof raw.stepIndex === "number" && Number.isFinite(raw.stepIndex)
      ? Math.max(0, Math.floor(raw.stepIndex))
      : 0;
  const completed = raw.completed === true;

  return {
    version: 5,
    flowMode: "fresh",
    stepIndex,
    answers,
    completed,
  };
}

/** Миграция v3 → v5: устаревший режим stuck превращаем в clarify с чистыми ответами. */
function migrateV3ToV5(raw: Record<string, unknown>): QuizPersistedState | null {
  if (typeof raw.stepIndex !== "number" || !Number.isFinite(raw.stepIndex)) return null;
  if (!isRecord(raw.answers)) return null;
  if (typeof raw.completed !== "boolean") return null;

  const fm = raw.flowMode;
  if (fm === "stuck") {
    return {
      version: 5,
      flowMode: "clarify",
      stepIndex: 0,
      answers: {},
      completed: false,
    };
  }
  if (fm === "fresh" || fm === "clarify") {
    return {
      version: 5,
      flowMode: fm,
      stepIndex: Math.max(0, Math.floor(raw.stepIndex)),
      answers: raw.answers as QuizAnswers,
      completed: raw.completed,
    };
  }
  if (fm === null) {
    return {
      version: 5,
      flowMode: null,
      stepIndex: Math.max(0, Math.floor(raw.stepIndex)),
      answers: raw.answers as QuizAnswers,
      completed: raw.completed,
    };
  }
  return null;
}

function parsePersistedBody(
  fm: FlowMode | null,
  stepIndex: number,
  answers: QuizAnswers,
  completed: boolean,
): QuizPersistedState {
  const migrated = migrateInProgressLegacyFreshQuiz(fm, completed, stepIndex, answers);
  const idx = Math.max(0, Math.floor(migrated.stepIndex));
  const ans = migrated.answers;

  const base: QuizPersistedState = {
    version: 5,
    flowMode: fm,
    stepIndex: idx,
    answers: ans,
    completed,
  };
  if (
    base.flowMode === "clarify" &&
    base.answers.clarifyStage1 == null &&
    !isLegacyClarifyQuizComplete(base.answers) &&
    (base.stepIndex > 0 || base.completed)
  ) {
    return {
      ...base,
      stepIndex: 0,
      completed: false,
    };
  }
  return base;
}

function parsePersistedQuiz(raw: unknown): QuizPersistedState | null {
  if (!isRecord(raw)) return null;

  if (raw.version === 5) {
    const fm = raw.flowMode;
    if (fm !== "fresh" && fm !== "clarify" && fm !== null) return null;
    if (typeof raw.stepIndex !== "number" || !Number.isFinite(raw.stepIndex)) return null;
    if (!isRecord(raw.answers)) return null;
    if (typeof raw.completed !== "boolean") return null;
    return parsePersistedBody(
      fm as FlowMode | null,
      raw.stepIndex,
      raw.answers as QuizAnswers,
      raw.completed,
    );
  }

  if (raw.version === 4) {
    const fm = raw.flowMode;
    if (fm !== "fresh" && fm !== "clarify" && fm !== null) return null;
    if (typeof raw.stepIndex !== "number" || !Number.isFinite(raw.stepIndex)) return null;
    if (!isRecord(raw.answers)) return null;
    if (typeof raw.completed !== "boolean") return null;
    return parsePersistedBody(
      fm as FlowMode | null,
      raw.stepIndex,
      raw.answers as QuizAnswers,
      raw.completed,
    );
  }

  if (raw.version === 3) {
    return migrateV3ToV5(raw);
  }

  if (raw.version === 2) {
    return migrateV2ToV5(raw);
  }

  return null;
}

export const defaultQuizState = (): QuizPersistedState => ({
  version: 5,
  flowMode: null,
  stepIndex: 0,
  answers: {},
  completed: false,
});

export function loadQuizState(): QuizPersistedState | null {
  if (typeof window === "undefined") return null;
  try {
    if (window.localStorage.getItem(LEGACY_KEY)) {
      window.localStorage.removeItem(LEGACY_KEY);
    }
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return parsePersistedQuiz(JSON.parse(raw) as unknown);
  } catch {
    return null;
  }
}

export function saveQuizState(state: QuizPersistedState): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    /* quota / private mode */
  }
}

export function clearQuizState(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(STORAGE_KEY);
  window.localStorage.removeItem(LEGACY_KEY);
}
