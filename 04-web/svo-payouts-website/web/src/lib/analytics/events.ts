/** Имена событий для GA4 (gtag) и целей Яндекс.Метрики (reachGoal). */
export const ANALYTICS_EVENTS = {
  fresh_flow_selected: "fresh_flow_selected",
  stuck_flow_selected: "stuck_flow_selected",
  quiz_start: "quiz_start",
  quiz_clarify_to_fresh: "quiz_clarify_to_fresh",
  quiz_complete: "quiz_complete",
  result_view: "result_view",
  lead_form_start: "lead_form_start",
  lead_form_submit: "lead_form_submit",
  lead_form_success: "lead_form_success",
} as const;

export type AnalyticsEventName = keyof typeof ANALYTICS_EVENTS;
