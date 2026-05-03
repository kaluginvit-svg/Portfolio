import type {
  ClarifyGoalPrimary,
  ClarifyGoalSecondary,
  ClarifyPostFilingFeedback,
  ClarifyStage1,
  ClarifyCopiesStatus,
  ClarifyDeathCertStatus,
  ClarifyFilingStatus,
  ClarifyKinshipDocsStatus,
  ClarifyMilitaryNoticeStatus,
  ClarifyWhereSubmitted,
} from "@/types/quiz";

export const clarifyStage1Options: { id: ClarifyStage1; label: string }[] = [
  { id: "start", label: "Я только начинаю разбираться" },
  { id: "collecting_docs", label: "Уже собираю документы" },
  {
    id: "ready_to_file",
    label: "Документы почти готовы, хочу понять, куда и как подавать",
  },
  { id: "already_filed", label: "Уже подавал(а) документы" },
  {
    id: "post_filing_problem",
    label: "После подачи возникла проблема или непонятная ситуация",
  },
];

export const clarifyDeathCertOptions: {
  id: ClarifyDeathCertStatus;
  label: string;
}[] = [
  { id: "yes", label: "Да, уже на руках" },
  { id: "in_progress", label: "Оформляем, ещё в процессе" },
  { id: "no", label: "Пока нет" },
];

export const clarifyMilitaryNoticeOptions: {
  id: ClarifyMilitaryNoticeStatus;
  label: string;
}[] = [
  { id: "yes", label: "Да, есть" },
  { id: "requested_waiting", label: "Запрашивали, ждём" },
  { id: "no", label: "Пока нет" },
  { id: "unsure", label: "Не понимаю, какой именно документ нужен" },
];

export const clarifyKinshipOptions: {
  id: ClarifyKinshipDocsStatus;
  label: string;
}[] = [
  { id: "complete", label: "Да, всё собрано" },
  { id: "partial", label: "Есть часть документов" },
  { id: "none", label: "Пока нет" },
  { id: "unsure", label: "Не понимаю, чего именно не хватает" },
];

export const clarifyCopiesOptions: {
  id: ClarifyCopiesStatus;
  label: string;
}[] = [
  { id: "ready", label: "Да, всё основное готово" },
  { id: "collecting", label: "Частично готово, ещё собираем" },
  {
    id: "missing_details",
    label: "Не хватает отдельных документов или сведений",
  },
  {
    id: "need_guidance",
    label: "Не понимаю, что должно входить в полный пакет",
  },
];

export const clarifyFilingOptions: {
  id: ClarifyFilingStatus;
  label: string;
  hint?: string;
}[] = [
  {
    id: "not_yet",
    label: "Нет, ещё не подавали",
    hint: "Только готовите или передавали без официальной регистрации обращения.",
  },
  {
    id: "partial",
    label: "Подавали часть документов",
    hint: "В инстанции зарегистрировано не всё, что планировали.",
  },
  {
    id: "full_waiting",
    label: "Подали полный пакет",
    hint: "Есть основание считать, что комплект у ведомства и идёт рассмотрение.",
  },
  {
    id: "unclear_submission",
    label: "Что-то передавали, но не уверен(а), что это считается официальной подачей",
    hint: "Нужно отделить «устно передали» от зарегистрированного обращения.",
  },
];

/** Полный справочник (в т.ч. not_yet) — для сводки и старых ответов. */
export const clarifyWhereOptions: {
  id: ClarifyWhereSubmitted;
  label: string;
}[] = [
  { id: "not_yet", label: "Не подавали официально" },
  { id: "military_unit", label: "В воинскую часть" },
  { id: "voenkomat", label: "В военкомат" },
  { id: "sfr_mfc", label: "В СФР или МФЦ" },
  { id: "sogaz", label: "По страховой линии / в СОГАЗ" },
  { id: "several", label: "В несколько мест" },
  { id: "other", label: "В другое место" },
];

/** Куда подавали — только при filing ≠ not_yet (UI шага clarify_doc_6). */
export const clarifyWhereSubmittedOnlyOptions: {
  id: Exclude<ClarifyWhereSubmitted, "not_yet">;
  label: string;
}[] = [
  { id: "military_unit", label: "В воинскую часть" },
  { id: "voenkomat", label: "В военкомат" },
  { id: "sfr_mfc", label: "В СФР или МФЦ" },
  { id: "sogaz", label: "По страховой линии / в СОГАЗ" },
  { id: "several", label: "В несколько мест" },
  { id: "other", label: "В другое место" },
];

export const clarifyPostFilingFeedbackOptions: {
  id: ClarifyPostFilingFeedback;
  label: string;
  hint?: string;
}[] = [
  { id: "just_waiting", label: "Просто ждём, ответа ещё нет" },
  {
    id: "waiting_too_long",
    label: "Ждём уже слишком долго",
    hint: "Нет движения заметно дольше, чем ожидали.",
  },
  {
    id: "need_more_documents",
    label: "Попросили донести документы",
  },
  { id: "refusal", label: "Получили отказ" },
  { id: "partial_payment", label: "Пришла только часть выплат" },
  {
    id: "response_unclear",
    label: "Был ответ, но не понимаю, что он означает",
  },
];

export const clarifyGoalPrimaryOptions: {
  id: ClarifyGoalPrimary;
  label: string;
}[] = [
  { id: "no_start", label: "Не понимаю, с чего начать" },
  { id: "missing_docs", label: "Не понимаю, каких документов не хватает" },
  {
    id: "filing_order",
    label: "Не понимаю, куда и в каком порядке подавать",
  },
  {
    id: "after_filing",
    label: "Не понимаю, что делать после подачи",
  },
  {
    id: "authority_response",
    label: "Не понимаю ответ ведомства",
  },
];

export const clarifyGoalSecondaryOptions: {
  id: ClarifyGoalSecondary;
  label: string;
}[] = [
  { id: "next_steps", label: "Пошагово понять, что делать дальше" },
  { id: "check_package", label: "Проверить, всё ли готово по документам" },
  { id: "find_blocker", label: "Понять, где сейчас застопорилось дело" },
  { id: "full_overview", label: "Получить общую картину по моей ситуации" },
];

export const clarifyStepQuestions: Record<string, string> = {
  clarify_stage_1: "Что сейчас лучше всего описывает вашу ситуацию?",
  clarify_doc_1: "Есть ли у вас свидетельство о смерти?",
  clarify_doc_2:
    "Есть ли у вас извещение из части или другой документ по обстоятельствам?",
  clarify_doc_3: "Есть ли у вас документы, подтверждающие родство?",
  clarify_doc_4:
    "Кроме основных документов, всё ли готово для подачи заявления?",
  clarify_doc_5: "Уже подавали документы официально?",
  clarify_doc_6: "Куда вы подавали документы?",
  clarify_feedback_1: "Что сейчас происходит после подачи?",
  clarify_goal_1: "Что сейчас мешает больше всего?",
  clarify_goal_2: "Что вам сейчас нужнее всего?",
};

/** Короткие пояснения под заголовком шага. */
export const clarifyStepHints: Partial<Record<string, string>> = {
  clarify_doc_5:
    "От ответа зависит, задаём ли вопросы про конкретное ведомство и ситуацию после подачи.",
  clarify_doc_6:
    "Выберите основной канал, куда ушёл пакет или заявление в первую очередь.",
  clarify_feedback_1:
    "Это помогает понять, на каком этапе вы сейчас — ожидание, доработка или разбор ответа.",
  clarify_goal_1:
    "Честный ответ здесь экономит время на созвоне: сразу видно, куда копать глубже.",
  clarify_goal_2:
    "Можно выбрать то, что снимет тревожность быстрее всего — без обещания конкретного исхода.",
};

export const clarifyQuizCopy = {
  badge: "Документы",
  routePinned: "Маршрут зафиксирован",
  progressHint: "документы и подача",
  tapToContinue: "Выберите вариант — следующий шаг откроется сразу.",
  doneTitle: "Спасибо! Теперь ситуация ясна. Я могу помочь.",
  doneBody:
    "Когда будете готовы узнать предварительный расчёт выплат — запустите второй короткий опрос. А пока можете оставить контакты: разберём пакет, подачу и то, на что стоит обратить внимание в вашем случае.",
  ctaLead: "Оставить контакты",
  ctaCalculator: "Узнать, какие выплаты положены",
  again: "Пройти опрос про документы заново",
  /** Структурный блок после опроса (аналитический модуль). */
  diagnosticBlocks: [
    {
      title: "Что зафиксировано",
      body: "Сегмент пути, свидетельство, документ из части, родство и готовность пакета — как опорная картина, без оценки исхода.",
    },
    {
      title: "Что уже подано",
      body: "Статус официальной подачи и маршрут — чтобы не смешивать «передали» и зарегистрированное обращение.",
    },
    {
      title: "Где возможное узкое место",
      body: "Часто это неполный пакет, разные треки (часть / СФР / страховщик) или ожидание ответа без ясной отметки о приёме.",
    },
    {
      title: "Что важно проверить дальше",
      body: "Статус у адресата, перечень недостающего при ответе «донести», раздельный учёт по каждому основанию выплат.",
    },
  ] as const,
} as const;
