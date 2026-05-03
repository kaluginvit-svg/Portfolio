/** Результат разбора ответов квиза для CRM / вебхука / Telegram. */
export interface ClarifyInsightPayload {
  raw_answers: Record<string, string | undefined>;
  stage_score: number;
  stage_label: string;
  /** Человекочитаемая фаза воронки (см. словарь в ТЗ). */
  journey_phase: string;
  lead_temperature: string;
  death_certificate_status: string;
  military_notice_status: string;
  kinship_docs_status: string;
  submission_pack_status: string;
  filing_status: string;
  filing_route: string;
  current_case_state: string;
  /** Ключ для правил и отладки */
  primary_blocker_key: ClarifyPrimaryBlockerKey;
  /** Подпись из словаря primary_blocker */
  primary_blocker: string;
  /** Доп. строка под главным стопором или пусто */
  secondary_blocker_line: string;
  user_focus: string;
  consultant_summary: string;
  consultant_step_1: string;
  consultant_step_2: string;
  consultant_step_3: string;
  /** Многострочный текст по шаблону ТЗ (plain). */
  telegram_summary_plain: string;
}

export type ClarifyPrimaryBlockerKey =
  | "no_start"
  | "missing_death_certificate"
  | "missing_military_notice"
  | "kinship_gap"
  | "package_unclear"
  | "not_filed_yet"
  | "partial_filing"
  | "waiting_after_filing"
  | "response_after_filing";

export type ClarifyCurrentCaseStateKey =
  | "start_no_action"
  | "collecting_documents"
  | "almost_ready"
  | "partial_filing"
  | "full_waiting"
  | "waiting_too_long"
  | "need_more_documents"
  | "refusal_received"
  | "partial_payment_received"
  | "response_unclear"
  | "multiple_routes_confusion";
