import {
  isLegacyClarifyQuizComplete,
  isNewClarifyQuizComplete,
} from "@/lib/quiz/clarify-complete";
import { clarifyHasOfficialFiling } from "@/lib/quiz/steps";
import type {
  ClarifyCurrentCaseStateKey,
  ClarifyInsightPayload,
  ClarifyPrimaryBlockerKey,
} from "@/types/clarify-insight";
import type {
  ClarifyConsequenceFocus,
  ClarifyCopiesStatus,
  ClarifyDeathCertStatus,
  ClarifyFilingStatus,
  ClarifyGoalPrimary,
  ClarifyGoalSecondary,
  ClarifyKinshipDocsStatus,
  ClarifyMilitaryNoticeStatus,
  ClarifyPostFilingFeedback,
  ClarifyStage1,
  ClarifyWhereSubmitted,
  QuizAnswers,
} from "@/types/quiz";

const JOURNEY_PHASE_LABEL: Record<string, string> = {
  start: "До подачи",
  document_collection: "До подачи",
  ready_to_file: "Подготовка к подаче",
  filing_in_progress: "Подача",
  post_filing: "После подачи",
};

const LEAD_TEMP_LABEL: Record<string, string> = {
  cold: "Холодный лид",
  warm: "Тёплый лид",
  hot: "Горячий лид",
};

const DEATH_CERT_LABEL: Record<ClarifyDeathCertStatus, string> = {
  yes: "есть",
  in_progress: "оформляют, ждут",
  no: "нет",
};

const MILITARY_LABEL: Record<ClarifyMilitaryNoticeStatus, string> = {
  yes: "есть",
  requested_waiting: "запросили, ждут",
  no: "нет",
  unsure: "не понимают, какой документ нужен",
};

const KINSHIP_LABEL: Record<ClarifyKinshipDocsStatus, string> = {
  complete: "собраны",
  partial: "частично собраны",
  none: "нет",
  unsure: "не понимают, чего не хватает",
};

const PACK_LABEL: Record<ClarifyCopiesStatus, string> = {
  ready: "готов",
  collecting: "ещё в работе",
  missing_details: "не хватает отдельных документов или сведений",
  need_guidance: "не понимают, что входит в пакет",
};

const FILING_STATUS_LABEL: Record<ClarifyFilingStatus, string> = {
  not_yet: "Официально не подавали",
  partial: "Подавали часть документов",
  full_waiting: "Подали полный пакет",
  had_feedback:
    "Уже были ответы ведомства (старый формат ответа — уточнить детали)",
  unclear_submission: "Что-то передавали, но статус подачи неясен",
};

const FILING_ROUTE_LABEL: Record<ClarifyWhereSubmitted, string> = {
  not_yet: "не подавали",
  military_unit: "воинская часть",
  voenkomat: "военкомат",
  sfr_mfc: "СФР / МФЦ",
  sogaz: "СОГАЗ / страховая линия",
  several: "в несколько мест",
  other: "другое место",
};

const CASE_STATE_LABEL: Record<ClarifyCurrentCaseStateKey, string> = {
  start_no_action: "Человек ещё не начал практические действия",
  collecting_documents: "Человек собирает документы и не может перейти к подаче",
  almost_ready:
    "Документы в основном собраны, но человек не вышел на подачу",
  partial_filing: "Подача началась, но пакет ещё не завершён",
  full_waiting: "Полный пакет подан, сейчас идёт ожидание",
  waiting_too_long: "После подачи слишком долго нет движения",
  need_more_documents: "После подачи попросили донести документы",
  refusal_received: "После подачи получен отказ",
  partial_payment_received: "После подачи пришла только часть выплат",
  response_unclear: "После подачи получен ответ, но его смысл непонятен",
  multiple_routes_confusion:
    "Человек обращался в несколько мест и запутался в маршруте",
};

const PRIMARY_BLOCKER_LABEL: Record<ClarifyPrimaryBlockerKey, string> = {
  no_start: "Не начинал путь",
  missing_death_certificate: "Нет свидетельства о смерти",
  missing_military_notice: "Нет документа из части",
  kinship_gap: "Не до конца закрыт вопрос по родству",
  package_unclear: "Неясен состав полного пакета",
  not_filed_yet: "Официальной подачи ещё не было",
  partial_filing: "Подали только часть документов",
  waiting_after_filing: "Слишком долго нет движения после подачи",
  response_after_filing: "Есть проблемный ответ после подачи",
};

const GOAL_PRIMARY_LABEL: Record<ClarifyGoalPrimary, string> = {
  no_start: "Не понимаю, с чего начать",
  missing_docs: "Не понимаю, каких документов не хватает",
  filing_order: "Не понимаю, куда и в каком порядке подавать",
  after_filing: "Не понимаю, что делать после подачи",
  authority_response: "Не понимаю ответ ведомства",
};

const GOAL_SECONDARY_LABEL: Record<ClarifyGoalSecondary, string> = {
  next_steps: "Пошагово понять, что делать дальше",
  check_package: "Проверить, всё ли готово по документам",
  find_blocker: "Понять, где сейчас застопорилось дело",
  full_overview: "Получить общую картину по ситуации",
};

export const consultantStepsByPrimaryBlocker: Record<
  ClarifyPrimaryBlockerKey,
  readonly [string, string, string]
> = {
  no_start: [
    "Коротко обозначить типовой маршрут: документы → канал подачи → ожидание, без обещания сроков.",
    "Зафиксировать, какие документы уже есть и что обычно запрашивают в первую очередь.",
    "Договориться о следующем шаге: список недостающего или запись на разбор пакета.",
  ],
  missing_death_certificate: [
    "Уточнить стадию оформления ЗАГС и кто подаёт документы.",
    "Объяснить, как свидетельство связывается с остальными шагами (без давления по срокам).",
    "Согласовать, что клиент принесёт/пришлёт, когда документ будет на руках.",
  ],
  missing_military_notice: [
    "Выяснить, обращались ли в часть, есть ли номер обращения или ответ.",
    "Сопоставить с типовым набором: что обычно закрывает блок по обстоятельствам.",
    "Предложить понятный следующий шаг: повторный запрос, фиксация отказа, иной канал.",
  ],
  kinship_gap: [
    "Собрать состав семьи и текущие документы (копии/оригиналы).",
    "Обозначить, какие подтверждения родства обычно спрашивают по линии клиента.",
    "Сформировать чек-лист недостающего и порядок получения справок.",
  ],
  package_unclear: [
    "Сверить цель обращения и перечень оснований выплат по ситуации клиента.",
    "Дать структуру «полного пакета» без юридических гарантий исхода.",
    "Выделить 2–3 пункта, которые чаще всего возвращают на доработку.",
  ],
  not_filed_yet: [
    "Уточнить готовность пакета и куда логичнее нести первым шагом.",
    "Развести каналы (часть / СФР / страховая), если их несколько.",
    "Согласовать формат подачи и что сохранить как подтверждение приёма.",
  ],
  partial_filing: [
    "Зафиксировать, что уже принято и что осталось по каждому каналу.",
    "Проверить, нет ли дублирующих обращений, которые путают статус.",
    "Составить короткий план доноса с приоритетом документов.",
  ],
  waiting_after_filing: [
    "Уточнить дату подачи, способ (лично/онлайн/МФЦ) и есть ли отметка о приёме.",
    "Предложить сценарий запроса статуса у адресата без эскалации «в лоб».",
    "Если сроки критичны — обозначить типовые шаги фиксации бездействия (без обещания результата).",
  ],
  response_after_filing: [
    "Попросить текст ответа/уведомления или его суть своими словами.",
    "Сопоставить ответ с типовыми сценариями: доработка, отказ, частичное решение.",
    "Сформулировать 1–2 варианта следующего шага с учётом рисков и сроков.",
  ],
};

type Normalised = {
  stage1: ClarifyStage1;
  death: ClarifyDeathCertStatus;
  military: ClarifyMilitaryNoticeStatus;
  kinship: ClarifyKinshipDocsStatus;
  pack: ClarifyCopiesStatus;
  filing: ClarifyFilingStatus;
  where: ClarifyWhereSubmitted | undefined;
  feedback: ClarifyPostFilingFeedback | undefined;
  goalP: ClarifyGoalPrimary;
  goalS: ClarifyGoalSecondary;
};

function inferStage1Legacy(a: QuizAnswers): ClarifyStage1 {
  if (a.clarifyFilingStatus === "had_feedback") return "post_filing_problem";
  if (a.clarifyFilingStatus && a.clarifyFilingStatus !== "not_yet") {
    return "already_filed";
  }
  if (a.clarifyCopiesStatus === "ready" && a.clarifyFilingStatus === "not_yet") {
    return "ready_to_file";
  }
  return "collecting_docs";
}

function mapConsequenceToGoals(
  c: ClarifyConsequenceFocus | undefined,
): { goalP: ClarifyGoalPrimary; goalS: ClarifyGoalSecondary } {
  switch (c) {
    case "timelines_stages":
      return { goalP: "filing_order", goalS: "next_steps" };
    case "incomplete_package_effects":
      return { goalP: "missing_docs", goalS: "check_package" };
    case "after_authority_response":
      return { goalP: "authority_response", goalS: "find_blocker" };
    case "full_overview":
    default:
      return { goalP: "missing_docs", goalS: "full_overview" };
  }
}

function mapHadFeedbackToPostFiling(): ClarifyPostFilingFeedback {
  return "response_unclear";
}

function normaliseAnswers(a: QuizAnswers): Normalised | null {
  if (isNewClarifyQuizComplete(a)) {
    const filed = clarifyHasOfficialFiling(a.clarifyFilingStatus);
    return {
      stage1: a.clarifyStage1!,
      death: a.clarifyDeathCert!,
      military: a.clarifyMilitaryNotice!,
      kinship: a.clarifyKinshipDocs!,
      pack: a.clarifyCopiesStatus!,
      filing: a.clarifyFilingStatus!,
      where: filed ? a.clarifyWhereSubmitted : undefined,
      feedback: filed ? a.clarifyPostFilingFeedback : undefined,
      goalP: a.clarifyGoalPrimary!,
      goalS: a.clarifyGoalSecondary!,
    };
  }
  if (isLegacyClarifyQuizComplete(a)) {
    const filed = clarifyHasOfficialFiling(a.clarifyFilingStatus);
    const { goalP, goalS } = mapConsequenceToGoals(a.clarifyConsequenceFocus);
    let filing = a.clarifyFilingStatus!;
    let feedback: ClarifyPostFilingFeedback | undefined;
    if (filing === "had_feedback") {
      filing = "full_waiting";
      feedback = mapHadFeedbackToPostFiling();
    } else if (filed) {
      feedback = "just_waiting";
    }
    return {
      stage1: inferStage1Legacy(a),
      death: a.clarifyDeathCert!,
      military: a.clarifyMilitaryNotice!,
      kinship: a.clarifyKinshipDocs!,
      pack: a.clarifyCopiesStatus!,
      filing,
      where: a.clarifyWhereSubmitted!,
      feedback,
      goalP,
      goalS,
    };
  }
  return null;
}

function journeyPhaseKey(n: Normalised): keyof typeof JOURNEY_PHASE_LABEL {
  if (n.stage1 === "post_filing_problem") return "post_filing";
  if (n.feedback != null) return "post_filing";
  if (clarifyHasOfficialFiling(n.filing)) {
    if (n.filing === "partial") return "filing_in_progress";
    if (n.filing === "unclear_submission") return "filing_in_progress";
    return "post_filing";
  }
  if (n.stage1 === "ready_to_file") return "ready_to_file";
  if (n.stage1 === "already_filed") return "filing_in_progress";
  if (n.stage1 === "start") return "start";
  return "document_collection";
}

function leadTemperatureKey(n: Normalised): keyof typeof LEAD_TEMP_LABEL {
  let score = 0;
  if (n.stage1 === "post_filing_problem") score += 3;
  if (n.stage1 === "already_filed") score += 2;
  if (n.feedback === "refusal" || n.feedback === "waiting_too_long") score += 3;
  if (n.feedback === "need_more_documents" || n.feedback === "response_unclear") {
    score += 2;
  }
  if (n.feedback === "partial_payment") score += 2;
  if (n.goalP === "authority_response") score += 2;
  if (n.death === "yes" && n.kinship === "complete") score += 1;
  if (score >= 5) return "hot";
  if (score >= 2) return "warm";
  return "cold";
}

function computeStageScore(n: Normalised): number {
  let s = 0;
  switch (n.stage1) {
    case "start":
      s += 18;
      break;
    case "collecting_docs":
      s += 32;
      break;
    case "ready_to_file":
      s += 48;
      break;
    case "already_filed":
      s += 62;
      break;
    case "post_filing_problem":
      s += 72;
      break;
    default:
      s += 25;
  }
  if (n.death === "yes") s += 10;
  else if (n.death === "in_progress") s += 5;
  if (n.military === "yes") s += 6;
  else if (n.military === "requested_waiting") s += 3;
  if (n.kinship === "complete") s += 8;
  else if (n.kinship === "partial") s += 4;
  if (n.pack === "ready") s += 8;
  else if (n.pack === "collecting") s += 4;
  if (n.filing === "full_waiting") s += 12;
  else if (n.filing === "partial") s += 8;
  else if (n.filing === "unclear_submission") s += 6;
  if (n.feedback === "waiting_too_long" || n.feedback === "refusal") s += 10;
  return Math.min(100, Math.round(s));
}

function stageLabel(n: Normalised): string {
  const labels: Record<ClarifyStage1, string> = {
    start: "Только начинает разбираться",
    collecting_docs: "Собирает документы",
    ready_to_file: "Почти готов к подаче",
    already_filed: "Уже подавал документы",
    post_filing_problem: "Проблема после подачи",
  };
  return labels[n.stage1];
}

function resolveCurrentCaseState(n: Normalised): ClarifyCurrentCaseStateKey {
  if (clarifyHasOfficialFiling(n.filing) && n.feedback) {
    switch (n.feedback) {
      case "waiting_too_long":
        return "waiting_too_long";
      case "need_more_documents":
        return "need_more_documents";
      case "refusal":
        return "refusal_received";
      case "partial_payment":
        return "partial_payment_received";
      case "response_unclear":
        return "response_unclear";
      case "just_waiting":
        if (
          n.where === "several" &&
          (n.goalP === "filing_order" || n.goalS === "find_blocker")
        ) {
          return "multiple_routes_confusion";
        }
        return n.filing === "partial" ? "partial_filing" : "full_waiting";
      default:
        return n.filing === "partial" ? "partial_filing" : "full_waiting";
    }
  }
  if (
    clarifyHasOfficialFiling(n.filing) &&
    n.where === "several" &&
    (n.goalP === "filing_order" || n.goalS === "find_blocker")
  ) {
    return "multiple_routes_confusion";
  }
  if (n.filing === "partial") return "partial_filing";
  if (n.stage1 === "start" && n.death === "no" && n.kinship === "none") {
    return "start_no_action";
  }
  if (n.pack === "ready" && n.filing === "not_yet") return "almost_ready";
  return "collecting_documents";
}

function resolvePrimaryBlocker(n: Normalised): {
  key: ClarifyPrimaryBlockerKey;
  secondaryLine: string;
} {
  let secondaryLine = "";

  if (n.goalP === "no_start" && n.stage1 === "start") {
    return { key: "no_start", secondaryLine };
  }
  if (n.death === "no") {
    return { key: "missing_death_certificate", secondaryLine };
  }
  if (n.military === "no") {
    return { key: "missing_military_notice", secondaryLine };
  }
  if (n.kinship === "none" || n.kinship === "partial" || n.kinship === "unsure") {
    return { key: "kinship_gap", secondaryLine };
  }
  if (n.pack === "need_guidance") {
    return { key: "package_unclear", secondaryLine };
  }
  if (n.filing === "not_yet") {
    return { key: "not_filed_yet", secondaryLine };
  }
  if (n.filing === "partial") {
    return { key: "partial_filing", secondaryLine };
  }
  if (n.feedback === "waiting_too_long") {
    return { key: "waiting_after_filing", secondaryLine };
  }
  if (
    n.feedback === "need_more_documents" ||
    n.feedback === "refusal" ||
    n.feedback === "partial_payment" ||
    n.feedback === "response_unclear"
  ) {
    return { key: "response_after_filing", secondaryLine };
  }
  if (n.feedback === "just_waiting") {
    secondaryLine =
      "Уточнение по ответу клиента: ожидают ответа, без указания на чрезмерную задержку.";
    return { key: "waiting_after_filing", secondaryLine };
  }
  if (n.where === "several") {
    secondaryLine =
      "Клиент отмечал подачу в несколько мест — проверить согласованность маршрута.";
    return { key: "response_after_filing", secondaryLine };
  }
  return { key: "not_filed_yet", secondaryLine };
}

function buildConsultantSummary(
  n: Normalised,
  caseKey: ClarifyCurrentCaseStateKey,
  blockerKey: ClarifyPrimaryBlockerKey,
): string {
  const parts = [
    `Сегмент: ${stageLabel(n)}. Документы: свидетельство — ${DEATH_CERT_LABEL[n.death]}, из части — ${MILITARY_LABEL[n.military]}, родство — ${KINSHIP_LABEL[n.kinship]}. Пакет: ${PACK_LABEL[n.pack]}.`,
    `Подача: ${FILING_STATUS_LABEL[n.filing]}.`,
  ];
  if (clarifyHasOfficialFiling(n.filing) && n.where) {
    parts.push(`Маршрут: ${FILING_ROUTE_LABEL[n.where]}.`);
  }
  parts.push(`Состояние дела: ${CASE_STATE_LABEL[caseKey]}.`);
  parts.push(`Главный стопор: ${PRIMARY_BLOCKER_LABEL[blockerKey]}.`);
  parts.push(`Запрос клиента: ${GOAL_PRIMARY_LABEL[n.goalP]}; фокус: ${GOAL_SECONDARY_LABEL[n.goalS]}.`);
  return parts.join(" ");
}

function filingStatusDisplay(f: ClarifyFilingStatus): string {
  return FILING_STATUS_LABEL[f];
}

function filingRouteDisplay(
  n: Normalised,
): string {
  if (!clarifyHasOfficialFiling(n.filing)) return FILING_ROUTE_LABEL.not_yet;
  if (!n.where || n.where === "not_yet") return FILING_ROUTE_LABEL.not_yet;
  return FILING_ROUTE_LABEL[n.where];
}

export function buildClarifyInsightPayload(
  answers: QuizAnswers,
): ClarifyInsightPayload | null {
  const n = normaliseAnswers(answers);
  if (!n) return null;

  const caseKey = resolveCurrentCaseState(n);
  const { key: blockerKey, secondaryLine } = resolvePrimaryBlocker(n);
  const steps = consultantStepsByPrimaryBlocker[blockerKey];

  const raw: Record<string, string | undefined> = {
    clarifyStage1: n.stage1,
    clarifyDeathCert: n.death,
    clarifyMilitaryNotice: n.military,
    clarifyKinshipDocs: n.kinship,
    clarifyCopiesStatus: n.pack,
    clarifyFilingStatus: n.filing,
    clarifyWhereSubmitted: n.where,
    clarifyPostFilingFeedback: n.feedback,
    clarifyGoalPrimary: n.goalP,
    clarifyGoalSecondary: n.goalS,
  };

  const journeyKey = journeyPhaseKey(n);
  const journeyLabel =
    JOURNEY_PHASE_LABEL[journeyKey] ?? JOURNEY_PHASE_LABEL.document_collection;
  const tempKey = leadTemperatureKey(n);
  const tempLabel = LEAD_TEMP_LABEL[tempKey] ?? LEAD_TEMP_LABEL.warm;

  const stage_score = computeStageScore(n);
  const stage_label = stageLabel(n);
  const consultant_summary = buildConsultantSummary(n, caseKey, blockerKey);

  const user_focus = `${GOAL_PRIMARY_LABEL[n.goalP]}; ${GOAL_SECONDARY_LABEL[n.goalS]}`;

  const telegram_summary_plain = formatClarifyTelegramSummaryPlain({
    stage_label,
    stage_score,
    journey_phase: journeyLabel,
    lead_temperature: tempLabel,
    death_certificate_status: DEATH_CERT_LABEL[n.death],
    military_notice_status: MILITARY_LABEL[n.military],
    kinship_docs_status: KINSHIP_LABEL[n.kinship],
    submission_pack_status: PACK_LABEL[n.pack],
    filing_status: filingStatusDisplay(n.filing),
    filing_route: filingRouteDisplay(n),
    current_case_state: CASE_STATE_LABEL[caseKey],
    primary_blocker: PRIMARY_BLOCKER_LABEL[blockerKey],
    secondary_blocker_line: secondaryLine,
    user_focus,
    consultant_summary,
    consultant_step_1: steps[0],
    consultant_step_2: steps[1],
    consultant_step_3: steps[2],
  });

  return {
    raw_answers: raw,
    stage_score,
    stage_label,
    journey_phase: journeyLabel,
    lead_temperature: tempLabel,
    death_certificate_status: DEATH_CERT_LABEL[n.death],
    military_notice_status: MILITARY_LABEL[n.military],
    kinship_docs_status: KINSHIP_LABEL[n.kinship],
    submission_pack_status: PACK_LABEL[n.pack],
    filing_status: filingStatusDisplay(n.filing),
    filing_route: filingRouteDisplay(n),
    current_case_state: CASE_STATE_LABEL[caseKey],
    primary_blocker_key: blockerKey,
    primary_blocker: PRIMARY_BLOCKER_LABEL[blockerKey],
    secondary_blocker_line: secondaryLine,
    user_focus,
    consultant_summary,
    consultant_step_1: steps[0],
    consultant_step_2: steps[1],
    consultant_step_3: steps[2],
    telegram_summary_plain,
  };
}

export function formatClarifyTelegramSummaryPlain(p: {
  stage_label: string;
  stage_score: number;
  journey_phase: string;
  lead_temperature: string;
  death_certificate_status: string;
  military_notice_status: string;
  kinship_docs_status: string;
  submission_pack_status: string;
  filing_status: string;
  filing_route: string;
  current_case_state: string;
  primary_blocker: string;
  secondary_blocker_line: string;
  user_focus: string;
  consultant_summary: string;
  consultant_step_1: string;
  consultant_step_2: string;
  consultant_step_3: string;
}): string {
  const sec = p.secondary_blocker_line.trim()
    ? `— ${p.secondary_blocker_line.trim()}`
    : "";
  return [
    "Новая заявка из квиза",
    "",
    `Этап: ${p.stage_label} — ${p.stage_score}/100`,
    `Фаза: ${p.journey_phase}`,
    `Приоритет: ${p.lead_temperature}`,
    "",
    "Что уже есть:",
    `— Свидетельство о смерти: ${p.death_certificate_status}`,
    `— Документ из части: ${p.military_notice_status}`,
    `— Документы о родстве: ${p.kinship_docs_status}`,
    `— Пакет для подачи: ${p.submission_pack_status}`,
    "",
    "Статус подачи:",
    `— ${p.filing_status}`,
    `— Куда подавали: ${p.filing_route}`,
    "",
    "Что происходит сейчас:",
    `— ${p.current_case_state}`,
    "",
    "Главный стопор:",
    `— ${p.primary_blocker}`,
    sec,
    "",
    "Что хочет понять:",
    `— ${p.user_focus}`,
    "",
    "Кратко для консультанта:",
    p.consultant_summary,
    "",
    "Что сделать консультанту:",
    `1. ${p.consultant_step_1}`,
    `2. ${p.consultant_step_2}`,
    `3. ${p.consultant_step_3}`,
  ]
    .filter((line) => line !== "")
    .join("\n");
}
