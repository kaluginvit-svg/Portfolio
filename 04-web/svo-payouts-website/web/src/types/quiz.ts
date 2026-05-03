/** Режим: полный расчёт выплат или короткий опрос только про документы (без расчёта на сайте). */
export type FlowMode = "fresh" | "clarify";

export type DeceasedRole =
  | "contract"
  | "mobilized"
  | "volunteer"
  | "rosgvardia"
  | "unknown";

export type Relation =
  | "spouse"
  | "mother"
  | "father"
  | "child_under_18"
  | "child_student"
  | "family_rep"
  | "complex";

export type RelationComplexSub =
  | "cohabitation_no_marriage"
  | "kinship_dispute"
  | "need_status_help";

export type Recipients =
  | "only_me"
  | "me_plus_1"
  | "me_plus_2"
  | "me_plus_3"
  | "me_plus_4_or_more";

export type RecipientsExact = "4" | "5" | "6" | "7_plus";

export type DocumentOption =
  | "death_cert"
  | "unit_notice"
  | "kinship_docs"
  | "almost_all"
  | "nothing_yet"
  | "unsure";

/** Новый квиз «расчёт выплат» (fresh). */
export type ServiceStatus =
  | "contract_mobilized"
  | "volunteer"
  | "force_department"
  | "unknown";

export type FreshApplicantRole =
  | "spouse_registered"
  | "cohabitation_no_marriage"
  | "parent"
  | "child_under_18"
  | "child_student_18_23"
  | "representative_or_unknown";

export type FreshRecipientsCount = "1" | "2" | "3" | "4" | "5_plus" | "unknown";

export type FreshChildrenCount = "0" | "1" | "2" | "3_plus";

export type DeathBasis = "duty" | "disease" | "unknown";

export type AmbiguityFlag = "no" | "yes" | "unknown";

export type CalcMode = "federal_only" | "federal_plus_region" | "unknown";

/** Устаревшие поля сценария B (могут прийти из старых лидов). */
export type StatusNow =
  | "no_response"
  | "incomplete_package"
  | "refusal"
  | "partial_paid"
  | "stuck_unknown";

export type SubmittedWhere =
  | "military_unit"
  | "voenkomat"
  | "sogaz"
  | "sfr_mfc"
  | "multiple";

export type WaitingOption = "lt1m" | "1to3m" | "3to6m" | "gt6m";

/** Блок «Прояснить ситуацию» — документы, подача, ориентиры по последствиям. */
export type ClarifyStage1 =
  | "start"
  | "collecting_docs"
  | "ready_to_file"
  | "already_filed"
  | "post_filing_problem";

export type ClarifyDeathCertStatus = "yes" | "in_progress" | "no";
export type ClarifyMilitaryNoticeStatus =
  | "yes"
  | "requested_waiting"
  | "no"
  | "unsure";
export type ClarifyKinshipDocsStatus = "complete" | "partial" | "none" | "unsure";
export type ClarifyCopiesStatus =
  | "ready"
  | "collecting"
  | "missing_details"
  | "need_guidance";

/** Уже подавали ли пакет / заявление официально. */
export type ClarifyFilingStatus =
  | "not_yet"
  | "partial"
  | "full_waiting"
  /** @deprecated в UI заменён на clarifyPostFilingFeedback; сохраняется в API для старых клиентов */
  | "had_feedback"
  | "unclear_submission";

/** Куда направляли (если ещё не подавали — отдельный пункт). */
export type ClarifyWhereSubmitted =
  | "not_yet"
  | "military_unit"
  | "voenkomat"
  | "sfr_mfc"
  | "sogaz"
  | "several"
  | "other";

/** Что важнее прояснить про дальнейшие шаги и последствия (не юридический исход). */
export type ClarifyConsequenceFocus =
  | "timelines_stages"
  | "incomplete_package_effects"
  | "after_authority_response"
  | "full_overview";

/** После подачи: что происходит сейчас (шаг clarify_feedback_1). */
export type ClarifyPostFilingFeedback =
  | "just_waiting"
  | "waiting_too_long"
  | "need_more_documents"
  | "refusal"
  | "partial_payment"
  | "response_unclear";

/** Что мешает больше всего (clarify_goal_1). */
export type ClarifyGoalPrimary =
  | "no_start"
  | "missing_docs"
  | "filing_order"
  | "after_filing"
  | "authority_response";

/** Что нужнее всего (clarify_goal_2). */
export type ClarifyGoalSecondary =
  | "next_steps"
  | "check_package"
  | "find_blocker"
  | "full_overview";

/** Шаг 1 диагностики «застрявшего» потока. */
export type StuckProblemType =
  | "no_response"
  | "incomplete_package"
  | "refusal"
  | "partial_paid"
  | "stuck_unknown"
  | "full_review";

/** Шаг 2: что уже подавали (multi). */
export type StuckSubmittedItem =
  | "main_application"
  | "docs_military_unit"
  | "docs_voenkomat"
  | "docs_sogaz"
  | "docs_sfr_mfc"
  | "complaints"
  | "unclear_submitted";

/** Шаг 3: куда обращались (multi). */
export type StuckSubmittedTo =
  | "military_unit"
  | "voenkomat"
  | "sogaz"
  | "sfr"
  | "mfc"
  | "social_region"
  | "prosecutor"
  | "court"
  | "multiple_unsure";

/** Шаг 4: ответы. */
export type StuckResponseStatus =
  | "silent"
  | "oral_wait"
  | "request_more_docs"
  | "written_refusal"
  | "partial_payments"
  | "unclear_response";

/** Шаг 5: интервал ожидания → далее в расчёт месяцев 1 / 2 / 4 / 6. */
export type StuckWaitingBucket = "lt1m" | "1to3m" | "3to6m" | "gt6m";

export interface QuizAnswers {
  /** @deprecated старый квиз fresh; сохраняется для API / localStorage */
  deceasedRole?: DeceasedRole;
  /** @deprecated */
  relation?: Relation;
  /** @deprecated */
  relationComplexSub?: RelationComplexSub;
  /** @deprecated */
  recipients?: Recipients;
  /** @deprecated */
  recipientsExact?: RecipientsExact;
  /** @deprecated */
  documents?: DocumentOption[];
  region?: string;

  /** Новый квиз расчёта выплат */
  serviceStatus?: ServiceStatus;
  freshApplicantRole?: FreshApplicantRole;
  freshRecipientsCount?: FreshRecipientsCount;
  freshChildrenCount?: FreshChildrenCount;
  deathBasis?: DeathBasis;
  ambiguityFlag?: AmbiguityFlag;
  calcMode?: CalcMode;
  /** @deprecated старый сценарий B; не используется в новом потоке */
  statusNow?: StatusNow;
  /** @deprecated */
  submittedWhere?: SubmittedWhere;
  /** @deprecated */
  waiting?: WaitingOption;

  stuckProblemType?: StuckProblemType;
  stuckSubmittedItems?: StuckSubmittedItem[];
  stuckSubmittedToList?: StuckSubmittedTo[];
  stuckResponseStatus?: StuckResponseStatus;
  /** 1 | 2 | 4 | 6 — после шага «сколько ждёте» */
  stuckMonthsWaiting?: number;

  /** Сегмент / этап пути (новый квиз, шаг clarify_stage_1). */
  clarifyStage1?: ClarifyStage1;
  clarifyDeathCert?: ClarifyDeathCertStatus;
  clarifyMilitaryNotice?: ClarifyMilitaryNoticeStatus;
  clarifyKinshipDocs?: ClarifyKinshipDocsStatus;
  clarifyCopiesStatus?: ClarifyCopiesStatus;
  clarifyFilingStatus?: ClarifyFilingStatus;
  clarifyWhereSubmitted?: ClarifyWhereSubmitted;
  /** @deprecated старый финальный шаг; при миграции маппится в clarifyGoal* */
  clarifyConsequenceFocus?: ClarifyConsequenceFocus;
  /** Только если была официальная подача (filing !== not_yet). */
  clarifyPostFilingFeedback?: ClarifyPostFilingFeedback;
  clarifyGoalPrimary?: ClarifyGoalPrimary;
  clarifyGoalSecondary?: ClarifyGoalSecondary;
}

export interface QuizPersistedState {
  version: 5;
  flowMode: FlowMode | null;
  stepIndex: number;
  answers: QuizAnswers;
  completed: boolean;
}

export type QuizStepId =
  | "clarify_stage_1"
  | "clarify_doc_1"
  | "clarify_doc_2"
  | "clarify_doc_3"
  | "clarify_doc_4"
  | "clarify_doc_5"
  | "clarify_doc_6"
  | "clarify_feedback_1"
  | "clarify_goal_1"
  | "clarify_goal_2"
  | "service_status"
  | "applicant_role"
  | "recipients_count"
  | "children_count"
  | "death_basis"
  | "ambiguity_flag"
  | "region"
  | "calc_mode";
