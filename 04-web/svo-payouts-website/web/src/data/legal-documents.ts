/**
 * Единый источник текста для страниц /privacy и /consent.
 * Файлы для скачивания — .docx в public/legal/ (см. legalDownloadHref).
 */
export const legalDocuments = {
  privacy: {
    h1: "Политика обработки персональных данных",
    paragraphs: [
      "Настоящий документ описывает общие принципы обработки персональных данных при использовании сайта и отправке заявки. Замените этот текст на утверждённую юристом политику: цели обработки, категории данных, сроки хранения, права субъекта, контакты оператора и порядок отзыва согласия.",
      "Оператор: укажите ИП/организацию, ИНН, ОГРН/ОГРНИП, адрес и email для обращений по вопросам ПДн.",
      "Данные из формы (имя, телефон, мессенджер, регион, описание ситуации) используются для связи с вами и предварительного анализа обращения, если вы дали согласие.",
    ],
  },
  consent: {
    h1: "Согласие на обработку персональных данных",
    paragraphs: [
      "Замените этот блок на юридически корректный текст согласия: кто оператор, какие данные обрабатываются, цели, сроки, способы отзыва согласия.",
      "Нажимая кнопку отправки формы на сайте и отмечая соответствующий чекбокс, пользователь подтверждает ознакомление с политикой и даёт согласие на обработку указанных персональных данных в заявленных целях.",
    ],
  },
} as const;

export type LegalDocId = keyof typeof legalDocuments;

/**
 * Имена .docx в `public/legal/` (как на диске).
 * Политика — страница /privacy; согласие — /consent.
 */
export const legalDownloadFilenames: Record<LegalDocId, string> = {
  privacy: "Политика конфиденциальности.docx",
  consent: "Согласие на обработку ПДн.docx",
};

function legalFilePublicUrl(filename: string): string {
  return `/legal/${encodeURIComponent(filename)}`;
}

/** URL для скачивания (кириллица в пути кодируется). */
export const legalDownloadHref: Record<LegalDocId, string> = {
  privacy: legalFilePublicUrl(legalDownloadFilenames.privacy),
  consent: legalFilePublicUrl(legalDownloadFilenames.consent),
};
