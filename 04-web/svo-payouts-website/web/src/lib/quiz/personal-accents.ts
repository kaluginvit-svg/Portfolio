import type { QuizAnswers } from "@/types/quiz";

export function getPersonalAccents(answers: QuizAnswers): string[] {
  const lines: string[] = [];

  if (answers.serviceStatus != null) {
    if (answers.ambiguityFlag === "yes" || answers.ambiguityFlag === "unknown") {
      lines.push(
        "В ответах отмечены неясности по семье или статусу — сумма на экране сопровождается пометкой «требует уточнений».",
      );
    }
    if (answers.freshRecipientsCount === "unknown") {
      lines.push(
        "Число получателей разовых выплат не задано — ориентир по личной доле на экране не считается точным.",
      );
    }
    if (answers.deathBasis === "unknown" && answers.freshChildrenCount && answers.freshChildrenCount !== "0") {
      lines.push(
        "Причина смерти уточняется: детская пенсия в ежемесячном блоке показана по верхнему ориентиру до проверки документов.",
      );
    }
    if (answers.freshApplicantRole === "cohabitation_no_marriage") {
      lines.push(
        "Незарегистрированный брак часто требует отдельной правовой оценки — разовые меры в расчёте даны как общий федеральный ориентир.",
      );
    }
  }

  if (answers.clarifyFilingStatus === "had_feedback") {
    lines.push(
      "Вы отмечали, что уже были ответы ведомств — при разговоре имеет смысл опереться на эту хронологию, чтобы не дублировать обращения.",
    );
  } else if (answers.clarifyFilingStatus === "full_waiting") {
    lines.push(
      "Пакет уже подан и в ожидании — ориентир по срокам ниже; на консультации можно сопоставить это с фактическими датами подачи.",
    );
  } else if (answers.clarifyFilingStatus === "partial") {
    lines.push(
      "Документы подавались частями — такие дела часто тянутся дольше; важно видеть, что уже зарегистрировано у адресата.",
    );
  }

  if (
    answers.clarifyWhereSubmitted != null &&
    answers.clarifyWhereSubmitted !== "not_yet" &&
    lines.length < 3
  ) {
    lines.push(
      "Направления подачи из короткого опроса сохранены в расчёте — это помогает не смешивать треки СФР, части и страховщика.",
    );
  }

  if (answers.deceasedRole === "unknown") {
    lines.push(
      "Статус погибшего пока неясен — от этого зависит, к каким основаниям опираться и куда идти первым шагом. На разговоре спокойно соберём, что уже знаете, и выберем логичный порядок действий.",
    );
  }

  if (answers.relation === "complex") {
    lines.push(
      "Нестандартный или спорный статус — не редкость. Важно аккуратно собрать, что подтверждает вашу связь с семьёй, и не спешить с обращениями вслепую — так меньше риск потерять время.",
    );
  }

  if (answers.documents?.includes("nothing_yet")) {
    lines.push(
      "Если документы ещё не трогали — ничего страшного: начнём с минимума того, какие бумаги нужны под вашу роль и регион, чтобы не бегать за лишними справками.",
    );
  }

  return lines.slice(0, 3);
}
