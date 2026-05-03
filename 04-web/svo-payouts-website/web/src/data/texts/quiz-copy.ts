import type {
  DeceasedRole,
  DocumentOption,
  RecipientsExact,
  Relation,
  RelationComplexSub,
  StatusNow,
  SubmittedWhere,
  WaitingOption,
} from "@/types/quiz";

export const deceasedOptions: { id: DeceasedRole; label: string }[] = [
  { id: "contract", label: "Служил по контракту" },
  { id: "mobilized", label: "Был мобилизован" },
  { id: "volunteer", label: "Доброволец" },
  { id: "rosgvardia", label: "Росгвардия или другое ведомство" },
  { id: "unknown", label: "Пока не уверен(а) / сложно сказать" },
];

export const relationOptions: { id: Relation; label: string }[] = [
  { id: "spouse", label: "Супруг или супруга" },
  { id: "mother", label: "Мать" },
  { id: "father", label: "Отец" },
  { id: "child_under_18", label: "Ребёнок до 18 лет" },
  { id: "child_student", label: "Ребёнок 18–23, очная учёба" },
  { id: "family_rep", label: "Представляю семью" },
  { id: "complex", label: "Ситуация нестандартная или спорная" },
];

export const relationComplexOptions: { id: RelationComplexSub; label: string }[] =
  [
    {
      id: "cohabitation_no_marriage",
      label: "Жили вместе, брак не оформляли",
    },
    { id: "kinship_dispute", label: "Есть вопросы или спор о родстве" },
    { id: "need_status_help", label: "Нужна помощь понять мой статус" },
  ];

export const recipientsOptions = [
  { id: "only_me" as const, label: "Только я" },
  { id: "me_plus_1" as const, label: "Я и ещё один человек" },
  { id: "me_plus_2" as const, label: "Я и ещё двое" },
  { id: "me_plus_3" as const, label: "Я и ещё трое" },
  { id: "me_plus_4_or_more" as const, label: "Четверо и больше" },
];

export const recipientsExactOptions: { id: RecipientsExact; label: string }[] = [
  { id: "4", label: "4" },
  { id: "5", label: "5" },
  { id: "6", label: "6" },
  { id: "7_plus", label: "7 и больше" },
];

export const documentOptions: { id: DocumentOption; label: string }[] = [
  { id: "death_cert", label: "Свидетельство о смерти" },
  { id: "unit_notice", label: "Извещение или документы из части" },
  { id: "kinship_docs", label: "Документы, подтверждающие родство" },
  { id: "almost_all", label: "Почти всё уже собрали" },
  { id: "nothing_yet", label: "Пока ничего не собирали" },
  { id: "unsure", label: "Пока не понимаю, что именно нужно" },
];

export const statusNowOptions: { id: StatusNow; label: string }[] = [
  { id: "no_response", label: "Тишина — ответа нет" },
  { id: "incomplete_package", label: "Сказали, что пакет неполный" },
  { id: "refusal", label: "Пришёл отказ" },
  { id: "partial_paid", label: "Часть выплат есть, части нет" },
  { id: "stuck_unknown", label: "Не понимаем, где застряло" },
];

export const submittedWhereOptions: { id: SubmittedWhere; label: string }[] = [
  { id: "military_unit", label: "В воинскую часть" },
  { id: "voenkomat", label: "В военкомат" },
  { id: "sogaz", label: "В СОГАЗ" },
  { id: "sfr_mfc", label: "В СФР или МФЦ" },
  { id: "multiple", label: "В несколько мест" },
];

export const waitingOptions: { id: WaitingOption; label: string }[] = [
  { id: "lt1m", label: "Меньше месяца" },
  { id: "1to3m", label: "От одного до трёх месяцев" },
  { id: "3to6m", label: "От трёх до шести месяцев" },
  { id: "gt6m", label: "Больше шести месяцев" },
];

export const stepQuestions: Record<string, string> = {
  deceased: "Кем на военной службе был ваш близкий человек?",
  relation: "Кем вы ему приходитесь?",
  relation_complex: "Что из этого ближе всего к вашей ситуации?",
  recipients: "Кто ещё из семьи может претендовать на выплаты вместе с вами?",
  recipients_count: "Сколько человек вместе с вами может претендовать на выплаты?",
  documents:
    "Что из документов уже есть на руках? Можно отметить несколько вариантов.",
  region: "В каком регионе вы живёте?",
};

/** Тексты интерфейса предварительного расчёта (подсказки, кнопки, ошибки). */
export const quizFlowCopy = {
  emptyTitle: "С чего начнём?",
  emptySubtitle:
    "Расчёт выплат — отдельный опрос. «Прояснить ситуацию» — про документы, факт подачи и ориентиры по дальнейшим шагам, без сумм на экране.",
  btnScenarioA: "Узнать, какие выплаты положены",
  btnScenarioB: "Прояснить ситуацию",
  badgeFresh: "Ориентир по выплатам",
  badgeClarify: "Документы и подача",
  clarifyProgressHint: "без расчёта сумм",
  resetQuiz: "Очистить расчёт",
  progressQuestion: (n: number, total: number) => `Шаг ${n} из ${total}`,
  next: "Далее",
  showResult: "Показать предварительный расчёт",
  tapToContinueFresh: "Выберите вариант — следующий шаг откроется сразу.",
  back: "Назад",
  documentsGroupAria: "Какие документы уже есть",
  submittedWhereHeading: "Куда уже относили документы или заявления",
  waitingHeading: "Сколько примерно ждёте",
  resetConfirm:
    "Сбросить ответы предварительного расчёта? Черновик в браузере будет удалён.",
  regionLabel: "Регион проживания",
  regionPlaceholder: "Например: Краснодарский край",
  regionHint:
    "Достаточно области, края или республики — так точнее ориентир по местным мерам поддержки.",
  validation: {
    pickOne: "Выберите один вариант — так расчёт будет ближе к делу",
    pickCloser: "Выберите вариант, который ближе всего",
    pickRecipients: "Укажите, пожалуйста, число получателей",
    documentsMin: "Отметьте хотя бы один пункт — даже «пока ничего» уже помогает",
    pickStatus: "Выберите, что сейчас происходит",
    pickWhere: "Выберите, куда уже обращались",
    pickWaiting: "Выберите примерный срок ожидания",
    submittedAndWaiting:
      "Нужны оба пункта: куда подавали и как долго ждёте",
    regionShort: "Напишите регион — хотя бы название области или края",
  },
} as const;
