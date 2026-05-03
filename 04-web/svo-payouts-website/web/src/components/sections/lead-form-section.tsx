"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { motion } from "framer-motion";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { Loader2, Lock, MessageCircleHeart, ShieldCheck } from "lucide-react";
import { useQuiz } from "@/contexts/quiz-context";
import { useUtmParams } from "@/hooks/use-utm";
import { legalDownloadHref } from "@/data/legal-documents";
import { leadForm, footerDisclaimer } from "@/data/texts/landing";
import { trackEvent } from "@/lib/analytics/track";
import { leadFormSchema, type LeadFormValues } from "@/lib/validation/lead";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export function LeadFormSection() {
  const router = useRouter();
  const utm = useUtmParams();
  const { state, reset: resetQuiz } = useQuiz();
  const [serverError, setServerError] = useState<string | null>(null);
  const leadFormStarted = useRef(false);

  const onLeadFormInteract = () => {
    if (leadFormStarted.current) return;
    leadFormStarted.current = true;
    trackEvent("lead_form_start", {});
  };

  const form = useForm<LeadFormValues>({
    resolver: zodResolver(leadFormSchema),
    defaultValues: {
      name: "",
      phone: "",
      email: "",
      messenger: "",
      region: state.answers.region ?? "",
      situation: "",
      consent: false,
    },
  });

  const {
    register,
    control,
    handleSubmit,
    setError,
    setValue,
    formState: { errors, isSubmitting },
  } = form;

  useEffect(() => {
    const r = state.answers.region?.trim();
    if (r) setValue("region", r, { shouldValidate: false, shouldDirty: false });
  }, [state.answers.region, setValue]);

  function firstNestedFieldMessage(value: unknown): string | undefined {
    if (typeof value === "string") return value;
    if (Array.isArray(value) && typeof value[0] === "string") return value[0];
    if (value && typeof value === "object") {
      for (const v of Object.values(value)) {
        const m = firstNestedFieldMessage(v);
        if (m) return m;
      }
    }
    return undefined;
  }

  const onSubmit = handleSubmit(async (values) => {
    setServerError(null);
    trackEvent("lead_form_submit", {});

    const body = {
      name: values.name,
      phone: values.phone,
      email: values.email,
      messenger: values.messenger,
      region: values.region,
      situation: values.situation,
      consent: values.consent,
      utm_source: utm.utm_source,
      utm_medium: utm.utm_medium,
      utm_campaign: utm.utm_campaign,
      quiz: {
        flowMode: state.flowMode,
        answers: state.answers,
        completed: state.completed,
      },
    };

    let res: Response;
    try {
      res = await fetch("/api/lead", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    } catch {
      setServerError(
        "Нет связи с сервером. Проверьте интернет и попробуйте снова.",
      );
      return;
    }

    let data: {
      ok?: boolean;
      success?: boolean;
      saved?: boolean;
      telegramSent?: boolean;
      webhookSent?: boolean;
      message?: string;
      fieldErrors?: Partial<Record<keyof LeadFormValues | string, string[]>> & {
        quiz?: unknown;
      };
      formErrors?: string[];
    };
    try {
      data = (await res.json()) as typeof data;
    } catch {
      setServerError(leadForm.submitErrorGeneric);
      return;
    }

    if (!res.ok || !data.ok || !data.success || !data.saved) {
      const fe = data.fieldErrors;
      let handled = false;
      if (fe) {
        const map: (keyof LeadFormValues)[] = [
          "name",
          "phone",
          "email",
          "messenger",
          "region",
          "situation",
          "consent",
        ];
        for (const key of map) {
          const msg = fe[key]?.[0];
          if (msg) {
            setError(key, { message: msg });
            handled = true;
          }
        }
        const skipQuiz = new Set<string>([
          "name",
          "phone",
          "email",
          "messenger",
          "region",
          "situation",
          "consent",
        ]);
        for (const [k, v] of Object.entries(fe)) {
          if (skipQuiz.has(k)) continue;
          const nested = firstNestedFieldMessage(v);
          if (nested) {
            setServerError(nested);
            handled = true;
            break;
          }
        }
      }
      if (data.formErrors?.length) {
        setServerError(data.formErrors.join(" "));
        handled = true;
      }
      if (!handled) {
        setServerError(data.message ?? leadForm.submitErrorGeneric);
      }
      return;
    }

    trackEvent("lead_form_success", {
      telegram_sent: data.telegramSent === true,
      webhook_sent: data.webhookSent === true,
    });
    resetQuiz();
    router.push("/thanks");
  });

  return (
    <section
      id="lead-form"
      className="ds-section-y scroll-mt-[4.5rem] border-b border-[var(--cool-border)] bg-[var(--main-bg)] px-4 min-[360px]:px-5 lg:px-8"
      aria-labelledby="lead-form-title"
    >
      <div className="mx-auto max-w-2xl">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-40px" }}
          transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
          className="text-center"
        >
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-[var(--cool-border)] bg-white text-[var(--deep-blue)] shadow-[var(--shadow-spec-card)]">
            <MessageCircleHeart className="h-7 w-7" strokeWidth={1.875} aria-hidden />
          </div>
          <p className="ds-section-kicker mt-6">{leadForm.kicker}</p>
          <h2 id="lead-form-title" className="ds-h2 mt-2 text-[var(--deep-blue)]">
            {leadForm.title}
          </h2>
          <p className="ds-body mx-auto mt-4 max-w-lg text-pretty">{leadForm.subtitle}</p>
          <ul className="mx-auto mt-6 flex flex-wrap justify-center gap-2 text-xs font-medium text-[var(--text-secondary)] md:text-sm">
            {leadForm.chips.map((text, i) => {
              const Icon = i === 0 ? ShieldCheck : Lock;
              return (
                <li
                  key={text}
                  className="inline-flex items-center gap-1.5 rounded-full border border-[var(--cool-border)] bg-white px-3 py-1.5 shadow-sm"
                >
                  <Icon className="h-3.5 w-3.5 text-[var(--deep-blue)]" strokeWidth={1.875} aria-hidden />
                  {text}
                </li>
              );
            })}
          </ul>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 18 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-20px" }}
          transition={{ delay: 0.08, duration: 0.48, ease: [0.22, 1, 0.36, 1] }}
          className="mt-10"
        >
          <Card className="relative overflow-hidden rounded-3xl border-[var(--cool-border)] shadow-[var(--shadow-spec-form)]">
            <CardHeader className="border-b border-[var(--light-blue-divider)] bg-[var(--neutral-surface)] pb-5 md:pb-6">
              <CardTitle className="text-base font-semibold text-[var(--deep-blue)] md:text-lg">
                {leadForm.sectionTitle}
              </CardTitle>
            </CardHeader>
            <CardContent className="bg-white pt-6 md:pt-8">
              <form
                className="space-y-6 md:space-y-7"
                onSubmit={onSubmit}
                onFocusCapture={onLeadFormInteract}
                noValidate
                aria-busy={isSubmitting}
              >
                <div className="grid gap-5 md:grid-cols-2 md:gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="lead-name" className="text-sm font-medium">
                      {leadForm.nameLabel}
                    </Label>
                    <Input
                      id="lead-name"
                      autoComplete="name"
                      placeholder={leadForm.namePlaceholder}
                      {...register("name")}
                      aria-invalid={!!errors.name}
                      aria-describedby={errors.name ? "lead-name-err" : undefined}
                    />
                    {errors.name ? (
                      <p id="lead-name-err" className="text-xs text-destructive">
                        {errors.name.message}
                      </p>
                    ) : null}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="lead-phone" className="text-sm font-medium">
                      {leadForm.phoneLabel}
                    </Label>
                    <Input
                      id="lead-phone"
                      type="tel"
                      inputMode="tel"
                      autoComplete="tel"
                      placeholder={leadForm.phonePlaceholder}
                      {...register("phone")}
                      aria-invalid={!!errors.phone}
                      aria-describedby={errors.phone ? "lead-phone-err" : undefined}
                    />
                    {errors.phone ? (
                      <p id="lead-phone-err" className="text-xs text-destructive">
                        {errors.phone.message}
                      </p>
                    ) : null}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="lead-email" className="text-sm font-medium">
                    {leadForm.emailLabel}{" "}
                    <span className="font-normal text-muted-foreground">
                      — {leadForm.emailOptional}
                    </span>
                  </Label>
                  <Input
                    id="lead-email"
                    type="email"
                    autoComplete="email"
                    placeholder={leadForm.emailPlaceholder}
                    {...register("email")}
                    aria-invalid={!!errors.email}
                    aria-describedby={errors.email ? "lead-email-err" : undefined}
                  />
                  {errors.email ? (
                    <p id="lead-email-err" className="text-xs text-destructive">
                      {errors.email.message}
                    </p>
                  ) : null}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="lead-messenger" className="text-sm font-medium">
                    {leadForm.messengerLabel}{" "}
                    <span className="font-normal text-muted-foreground">
                      — {leadForm.messengerOptional}
                    </span>
                  </Label>
                  <Input
                    id="lead-messenger"
                    placeholder={leadForm.messengerPlaceholder}
                    {...register("messenger")}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="lead-region" className="text-sm font-medium">
                    {leadForm.regionLabel}
                  </Label>
                  <Input
                    id="lead-region"
                    placeholder={leadForm.regionPlaceholder}
                    {...register("region")}
                    aria-invalid={!!errors.region}
                    aria-describedby={errors.region ? "lead-region-err" : undefined}
                  />
                  {errors.region ? (
                    <p id="lead-region-err" className="text-xs text-destructive">
                      {errors.region.message}
                    </p>
                  ) : null}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="lead-situation" className="text-sm font-medium">
                    {leadForm.situationLabel}{" "}
                    <span className="font-normal text-muted-foreground">
                      — {leadForm.situationOptional}
                    </span>
                  </Label>
                  <Textarea
                    id="lead-situation"
                    placeholder={leadForm.situationPlaceholder}
                    {...register("situation")}
                  />
                </div>

                <div className="rounded-xl border border-[var(--light-blue-divider)] bg-[var(--neutral-surface)] p-4 md:p-5">
                  <div className="flex gap-4">
                    <Controller
                      name="consent"
                      control={control}
                      render={({ field }) => (
                        <Checkbox
                          id="lead-consent"
                          checked={Boolean(field.value)}
                          onCheckedChange={(v) => field.onChange(v === true)}
                          onBlur={field.onBlur}
                          ref={field.ref}
                          aria-invalid={!!errors.consent}
                          className="mt-0.5"
                        />
                      )}
                    />
                    <div className="min-w-0 flex-1 space-y-2">
                      <label
                        htmlFor="lead-consent"
                        className="block cursor-pointer text-sm leading-relaxed text-foreground"
                      >
                        {leadForm.consentLead}{" "}
                        <span className="text-muted-foreground">
                          {leadForm.consentDocsIntro}
                        </span>
                      </label>
                      <p className="flex flex-wrap items-baseline gap-x-2 gap-y-1 text-sm">
                        <span className="inline-flex flex-wrap items-baseline gap-x-1.5">
                          <Link
                            href="/privacy"
                            className="font-medium text-[var(--deep-blue)] underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--deep-blue)_35%,transparent)] focus-visible:ring-offset-2 rounded-sm"
                          >
                            {leadForm.privacyLink}
                          </Link>
                          <a
                            href={legalDownloadHref.privacy}
                            download
                            className="text-xs font-medium text-muted-foreground underline-offset-4 hover:text-[var(--deep-blue)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--deep-blue)_35%,transparent)] focus-visible:ring-offset-2 rounded-sm"
                          >
                            {leadForm.legalDownloadShort}
                          </a>
                        </span>
                        <span className="text-[var(--text-secondary)]">·</span>
                        <span className="inline-flex flex-wrap items-baseline gap-x-1.5">
                          <Link
                            href="/consent"
                            className="font-medium text-[var(--deep-blue)] underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--deep-blue)_35%,transparent)] focus-visible:ring-offset-2 rounded-sm"
                          >
                            {leadForm.consentLink}
                          </Link>
                          <a
                            href={legalDownloadHref.consent}
                            download
                            className="text-xs font-medium text-muted-foreground underline-offset-4 hover:text-[var(--deep-blue)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--deep-blue)_35%,transparent)] focus-visible:ring-offset-2 rounded-sm"
                          >
                            {leadForm.legalDownloadShort}
                          </a>
                        </span>
                      </p>
                    </div>
                  </div>
                </div>
                {errors.consent ? (
                  <p className="text-xs text-destructive" role="alert">
                    {errors.consent.message}
                  </p>
                ) : null}

                {serverError ? (
                  <p
                    className="rounded-xl border border-[color-mix(in_srgb,var(--accent-red)_35%,var(--cool-border))] bg-[var(--soft-red-bg)] px-3.5 py-2.5 text-sm text-[var(--status-alert)]"
                    role="alert"
                    aria-live="assertive"
                  >
                    {serverError}
                  </p>
                ) : null}

                <Button
                  type="submit"
                  variant="cta"
                  size="touch"
                  className="text-base font-semibold sm:min-h-12"
                  disabled={isSubmitting}
                  aria-busy={isSubmitting}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2
                        className="size-5 shrink-0 animate-spin"
                        aria-hidden
                      />
                      {leadForm.submitSending}
                    </>
                  ) : (
                    leadForm.submit
                  )}
                </Button>
                <p className="text-center text-sm text-muted-foreground">
                  {leadForm.note}
                </p>
                <p className="text-center text-[11px] leading-relaxed text-muted-foreground/90">
                  {footerDisclaimer}
                </p>
              </form>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </section>
  );
}
