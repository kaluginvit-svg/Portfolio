import type {
  AmbiguityFlag,
  CalcMode,
  DeathBasis,
  FreshApplicantRole,
  FreshChildrenCount,
  FreshRecipientsCount,
  ServiceStatus,
} from "@/types/quiz";

export const serviceStatusOptions: { id: ServiceStatus; label: string }[] = [
  { id: "contract_mobilized", label: "Контрактник / мобилизованный" },
  { id: "volunteer", label: "Доброволец" },
  { id: "force_department", label: "Росгвардия / иное силовое ведомство" },
  { id: "unknown", label: "Не уверен(а)" },
];

export const freshApplicantRoleOptions: { id: FreshApplicantRole; label: string }[] = [
  { id: "spouse_registered", label: "Супруг(а), брак зарегистрирован" },
  { id: "cohabitation_no_marriage", label: "Жили вместе, но брак не регистрировали" },
  { id: "parent", label: "Мать / отец" },
  { id: "child_under_18", label: "Ребёнок до 18 лет" },
  { id: "child_student_18_23", label: "Ребёнок 18–23, учусь очно" },
  { id: "representative_or_unknown", label: "Представитель семьи / не уверен(а)" },
];

export const freshRecipientsCountOptions: { id: FreshRecipientsCount; label: string }[] = [
  { id: "1", label: "1" },
  { id: "2", label: "2" },
  { id: "3", label: "3" },
  { id: "4", label: "4" },
  { id: "5_plus", label: "5 и более" },
  { id: "unknown", label: "Не уверен(а)" },
];

export const freshChildrenCountOptions: { id: FreshChildrenCount; label: string }[] = [
  { id: "0", label: "Нет" },
  { id: "1", label: "1 ребёнок" },
  { id: "2", label: "2 ребёнка" },
  { id: "3_plus", label: "3 и более" },
];

export const deathBasisOptions: { id: DeathBasis; label: string }[] = [
  { id: "duty", label: "Гибель при исполнении обязанностей" },
  { id: "disease", label: "Смерть из-за заболевания, полученного при исполнении" },
  { id: "unknown", label: "Не уверен(а)" },
];

export const ambiguityFlagOptions: { id: AmbiguityFlag; label: string }[] = [
  { id: "no", label: "Нет, всё стандартно" },
  { id: "yes", label: "Да, есть спор / неясность" },
  { id: "unknown", label: "Не уверен(а)" },
];

export const calcModeOptions: { id: CalcMode; label: string }[] = [
  { id: "federal_only", label: "Только федеральный" },
  { id: "federal_plus_region", label: "Федеральный + региональный ориентир" },
  { id: "unknown", label: "Не знаю" },
];

export const freshStepQuestions: Record<string, string> = {
  service_status: "К какой категории относился погибший?",
  applicant_role: "Кто вы?",
  recipients_count:
    "Сколько всего человек входит в круг получателей разовых семейных выплат?",
  children_count: "Есть ли дети, для которых нужно считать ежемесячные выплаты?",
  death_basis: "Что известно о причине смерти?",
  ambiguity_flag:
    "Есть ли спор или неясность по браку, родству, составу семьи или статусу службы?",
  region: "В каком регионе вы живёте?",
  calc_mode: "Какой расчёт вам показать?",
};
