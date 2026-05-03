import { z } from "zod";
import { getRecipientsCount } from "@/lib/calculator";
import { isFreshQuizComplete } from "@/lib/calculator/fresh-payout-calculator";
import { isClarifyQuizComplete } from "@/lib/quiz/clarify-complete";
import { isLegacyFreshQuizComplete } from "@/lib/quiz/fresh-quiz-complete";
import type { QuizAnswers } from "@/types/quiz";

/** Поля формы (клиент + сервер). */
export const leadFormSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, "Укажите имя")
    .max(120, "Слишком длинное имя"),
  phone: z
    .string()
    .trim()
    .min(10, "Укажите номер телефона")
    .max(32, "Проверьте номер телефона")
    .refine(
      (s) => s.replace(/\D/g, "").length >= 10,
      "В номере должно быть не меньше 10 цифр",
    ),
  messenger: z
    .string()
    .trim()
    .max(120)
    .optional()
    .transform((v) => (v === "" ? undefined : v)),
  email: z
    .string()
    .trim()
    .max(254, "Слишком длинный email")
    .optional()
    .transform((v) => (v === "" || v === undefined ? undefined : v))
    .superRefine((val, ctx) => {
      if (val === undefined) return;
      const r = z.string().email().safeParse(val);
      if (!r.success) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Укажите корректный email",
        });
      }
    }),
  region: z
    .string()
    .trim()
    .min(1, "Укажите регион")
    .max(120),
  situation: z
    .string()
    .trim()
    .max(2000)
    .optional()
    .transform((v) => (v === "" ? undefined : v)),
  consent: z
    .boolean()
    .refine((v) => v === true, {
      message: "Нужно согласие на обработку персональных данных",
    }),
});

const deceasedRoleSchema = z.enum([
  "contract",
  "mobilized",
  "volunteer",
  "rosgvardia",
  "unknown",
]);
const relationSchema = z.enum([
  "spouse",
  "mother",
  "father",
  "child_under_18",
  "child_student",
  "family_rep",
  "complex",
]);
const relationComplexSubSchema = z.enum([
  "cohabitation_no_marriage",
  "kinship_dispute",
  "need_status_help",
]);
const recipientsSchema = z.enum([
  "only_me",
  "me_plus_1",
  "me_plus_2",
  "me_plus_3",
  "me_plus_4_or_more",
]);
const recipientsExactSchema = z.enum(["4", "5", "6", "7_plus"]);
const documentOptionSchema = z.enum([
  "death_cert",
  "unit_notice",
  "kinship_docs",
  "almost_all",
  "nothing_yet",
  "unsure",
]);
const statusNowSchema = z.enum([
  "no_response",
  "incomplete_package",
  "refusal",
  "partial_paid",
  "stuck_unknown",
]);
const submittedWhereSchema = z.enum([
  "military_unit",
  "voenkomat",
  "sogaz",
  "sfr_mfc",
  "multiple",
]);
const waitingSchema = z.enum(["lt1m", "1to3m", "3to6m", "gt6m"]);

const stuckProblemSchema = z.enum([
  "no_response",
  "incomplete_package",
  "refusal",
  "partial_paid",
  "stuck_unknown",
  "full_review",
]);
const stuckSubmittedItemSchema = z.enum([
  "main_application",
  "docs_military_unit",
  "docs_voenkomat",
  "docs_sogaz",
  "docs_sfr_mfc",
  "complaints",
  "unclear_submitted",
]);
const stuckSubmittedToSchema = z.enum([
  "military_unit",
  "voenkomat",
  "sogaz",
  "sfr",
  "mfc",
  "social_region",
  "prosecutor",
  "court",
  "multiple_unsure",
]);
const stuckResponseSchema = z.enum([
  "silent",
  "oral_wait",
  "request_more_docs",
  "written_refusal",
  "partial_payments",
  "unclear_response",
]);
const stuckMonthsSchema = z.union([
  z.literal(1),
  z.literal(2),
  z.literal(4),
  z.literal(6),
]);

const clarifyStage1Schema = z.enum([
  "start",
  "collecting_docs",
  "ready_to_file",
  "already_filed",
  "post_filing_problem",
]);
const clarifyDeathCertSchema = z.enum(["yes", "in_progress", "no"]);
const clarifyMilitarySchema = z.enum([
  "yes",
  "requested_waiting",
  "no",
  "unsure",
]);
const clarifyKinshipSchema = z.enum(["complete", "partial", "none", "unsure"]);
const clarifyCopiesSchema = z.enum([
  "ready",
  "collecting",
  "missing_details",
  "need_guidance",
]);
const clarifyFilingSchema = z.enum([
  "not_yet",
  "partial",
  "full_waiting",
  "had_feedback",
  "unclear_submission",
]);
const clarifyPostFilingFeedbackSchema = z.enum([
  "just_waiting",
  "waiting_too_long",
  "need_more_documents",
  "refusal",
  "partial_payment",
  "response_unclear",
]);
const clarifyGoalPrimarySchema = z.enum([
  "no_start",
  "missing_docs",
  "filing_order",
  "after_filing",
  "authority_response",
]);
const clarifyGoalSecondarySchema = z.enum([
  "next_steps",
  "check_package",
  "find_blocker",
  "full_overview",
]);
const clarifyWhereSchema = z.enum([
  "not_yet",
  "military_unit",
  "voenkomat",
  "sfr_mfc",
  "sogaz",
  "several",
  "other",
]);
const clarifyConsequenceSchema = z.enum([
  "timelines_stages",
  "incomplete_package_effects",
  "after_authority_response",
  "full_overview",
]);

const serviceStatusSchema = z.enum([
  "contract_mobilized",
  "volunteer",
  "force_department",
  "unknown",
]);
const freshApplicantRoleSchema = z.enum([
  "spouse_registered",
  "cohabitation_no_marriage",
  "parent",
  "child_under_18",
  "child_student_18_23",
  "representative_or_unknown",
]);
const freshRecipientsCountSchema = z.enum(["1", "2", "3", "4", "5_plus", "unknown"]);
const freshChildrenCountSchema = z.enum(["0", "1", "2", "3_plus"]);
const deathBasisSchema = z.enum(["duty", "disease", "unknown"]);
const ambiguityFlagSchema = z.enum(["no", "yes", "unknown"]);
const calcModeSchema = z.enum(["federal_only", "federal_plus_region", "unknown"]);

/** Не strict — лишние поля из старого localStorage отбрасываются без 400. */
export const quizAnswersApiSchema = z.object({
  deceasedRole: deceasedRoleSchema.optional(),
  relation: relationSchema.optional(),
  relationComplexSub: relationComplexSubSchema.optional(),
  recipients: recipientsSchema.optional(),
  recipientsExact: recipientsExactSchema.optional(),
  documents: z.array(documentOptionSchema).optional(),
  region: z.string().max(200).optional(),
  statusNow: statusNowSchema.optional(),
  submittedWhere: submittedWhereSchema.optional(),
  waiting: waitingSchema.optional(),
  stuckProblemType: stuckProblemSchema.optional(),
  stuckSubmittedItems: z.array(stuckSubmittedItemSchema).optional(),
  stuckSubmittedToList: z.array(stuckSubmittedToSchema).optional(),
  stuckResponseStatus: stuckResponseSchema.optional(),
  stuckMonthsWaiting: stuckMonthsSchema.optional(),
  clarifyStage1: clarifyStage1Schema.optional(),
  clarifyDeathCert: clarifyDeathCertSchema.optional(),
  clarifyMilitaryNotice: clarifyMilitarySchema.optional(),
  clarifyKinshipDocs: clarifyKinshipSchema.optional(),
  clarifyCopiesStatus: clarifyCopiesSchema.optional(),
  clarifyFilingStatus: clarifyFilingSchema.optional(),
  clarifyWhereSubmitted: clarifyWhereSchema.optional(),
  clarifyConsequenceFocus: clarifyConsequenceSchema.optional(),
  clarifyPostFilingFeedback: clarifyPostFilingFeedbackSchema.optional(),
  clarifyGoalPrimary: clarifyGoalPrimarySchema.optional(),
  clarifyGoalSecondary: clarifyGoalSecondarySchema.optional(),
  serviceStatus: serviceStatusSchema.optional(),
  freshApplicantRole: freshApplicantRoleSchema.optional(),
  freshRecipientsCount: freshRecipientsCountSchema.optional(),
  freshChildrenCount: freshChildrenCountSchema.optional(),
  deathBasis: deathBasisSchema.optional(),
  ambiguityFlag: ambiguityFlagSchema.optional(),
  calcMode: calcModeSchema.optional(),
});

export const quizPayloadSchema = z.object({
  /** `stuck` — устаревшее значение с клиента, на сервере обрабатывается как clarify */
  flowMode: z.enum(["fresh", "clarify", "stuck"]).nullable().optional(),
  scenario: z.enum(["A", "B"]).nullable().optional(),
  answers: quizAnswersApiSchema.optional(),
  completed: z.boolean().optional(),
});

/** Тело POST /api/lead */
export const leadApiSchema = leadFormSchema
  .extend({
    utm_source: z
      .string()
      .trim()
      .max(200)
      .optional()
      .transform((v) => (v === "" ? undefined : v)),
    utm_medium: z
      .string()
      .trim()
      .max(200)
      .optional()
      .transform((v) => (v === "" ? undefined : v)),
    utm_campaign: z
      .string()
      .trim()
      .max(200)
      .optional()
      .transform((v) => (v === "" ? undefined : v)),
    quiz: quizPayloadSchema.optional(),
  })
  .superRefine((data, ctx) => {
    const q = data.quiz;
    const mode = q?.flowMode;
    const flowOk =
      mode === "fresh" ||
      mode === "clarify" ||
      mode === "stuck" ||
      q?.scenario === "A" ||
      q?.scenario === "B";
    if (!flowOk) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message:
          "Сначала пройдите опрос на странице (расчёт выплат или блок про документы) и дойдите до конца — без этого заявку не принимаем.",
        path: ["quiz", "flowMode"],
      });
      return;
    }
    if (!q?.completed) return;

    const answers = (q?.answers ?? {}) as QuizAnswers;
    const clarifying =
      mode === "clarify" ||
      mode === "stuck" ||
      (mode == null && q.scenario === "B");

    if (clarifying) {
      if (isClarifyQuizComplete(answers)) return;
      if (answers.stuckProblemType != null || answers.statusNow != null) return;
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message:
          "Данные опроса про документы неполные — обновите страницу и пройдите шаги до конца.",
        path: ["quiz", "answers"],
      });
      return;
    }

    if (isFreshQuizComplete(answers) || isLegacyFreshQuizComplete(answers)) {
      const n = getRecipientsCount(answers);
      if (!Number.isFinite(n) || n < 1) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Некорректное число получателей в данных расчёта.",
          path: ["quiz", "answers", "recipients"],
        });
      }
      return;
    }

    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message:
        "Данные предварительного расчёта неполные — обновите страницу и пройдите опрос до конца.",
      path: ["quiz", "answers"],
    });
  });

export type LeadFormValues = z.input<typeof leadFormSchema>;
export type LeadApiPayload = z.output<typeof leadApiSchema>;
