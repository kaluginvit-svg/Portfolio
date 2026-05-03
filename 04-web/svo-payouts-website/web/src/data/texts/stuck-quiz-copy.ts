import type {
  StuckProblemType,
  StuckResponseStatus,
  StuckSubmittedItem,
  StuckSubmittedTo,
  StuckWaitingBucket,
} from "@/types/quiz";

export const stuckProblemOptions: { id: StuckProblemType; label: string }[] = [
  { id: "no_response", label: "Вообще нет ответа" },
  { id: "incomplete_package", label: "Сказали, что пакет неполный" },
  { id: "refusal", label: "Получили отказ" },
  { id: "partial_paid", label: "Пришла только часть выплат" },
  { id: "stuck_unknown", label: "Не понимаем, где зависло" },
  { id: "full_review", label: "Нужен разбор всей ситуации" },
];

export const stuckSubmittedItemOptions: { id: StuckSubmittedItem; label: string }[] = [
  { id: "main_application", label: "Заявление на основные выплаты" },
  { id: "docs_military_unit", label: "Документы в воинскую часть" },
  { id: "docs_voenkomat", label: "Документы в военкомат" },
  { id: "docs_sogaz", label: "Документы в СОГАЗ" },
  { id: "docs_sfr_mfc", label: "Документы в СФР / МФЦ" },
  { id: "complaints", label: "Жалобы / обращения" },
  { id: "unclear_submitted", label: "Пока ничего не понятно, что именно подавали" },
];

export const stuckSubmittedToOptions: { id: StuckSubmittedTo; label: string }[] = [
  { id: "military_unit", label: "Воинская часть" },
  { id: "voenkomat", label: "Военкомат" },
  { id: "sogaz", label: "СОГАЗ" },
  { id: "sfr", label: "СФР" },
  { id: "mfc", label: "МФЦ" },
  { id: "social_region", label: "Соцзащита региона" },
  { id: "prosecutor", label: "Прокуратура" },
  { id: "court", label: "Суд" },
  { id: "multiple_unsure", label: "В несколько мест, не уверены где что сейчас" },
];

export const stuckResponseOptions: { id: StuckResponseStatus; label: string }[] = [
  { id: "silent", label: "Нет, тишина" },
  { id: "oral_wait", label: "Устно сказали ждать" },
  { id: "request_more_docs", label: "Попросили донести документы" },
  { id: "written_refusal", label: "Пришёл письменный отказ" },
  { id: "partial_payments", label: "Пришла часть выплат" },
  { id: "unclear_response", label: "Не можем разобраться, что означал ответ" },
];

export const stuckWaitingOptions: { id: StuckWaitingBucket; label: string; months: number }[] =
  [
    { id: "lt1m", label: "До 1 месяца", months: 1 },
    { id: "1to3m", label: "1–3 месяца", months: 2 },
    { id: "3to6m", label: "3–6 месяцев", months: 4 },
    { id: "gt6m", label: "Больше 6 месяцев", months: 6 },
  ];

export const stuckStepQuestions: Record<string, string> = {
  stuck_problem: "Что сейчас происходит с вашим делом?",
  stuck_submitted_items: "Что вы уже подавали?",
  stuck_submitted_to: "Куда именно вы уже обращались?",
  stuck_response: "Были ли какие-то ответы?",
  stuck_waiting: "Сколько времени уже прошло?",
  stuck_bridge: "Спасибо. Теперь покажу предварительный расчёт выплат и отмечу, на что в вашей ситуации стоит обратить особое внимание.",
};

export const stuckQuizCopy = {
  multiHint: "Можно выбрать несколько вариантов.",
  bridgeBody:
    "Дальше — те же вопросы, что и при первой оценке выплат: они нужны, чтобы корректно показать состав сумм и долю. Это не повтор ради формы — без них расчёт будет неполным.",
  nextToCalculator: "Перейти к расчёту выплат",
};
