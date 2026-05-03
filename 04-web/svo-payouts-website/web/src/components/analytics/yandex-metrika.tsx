import Script from "next/script";

type Props = {
  counterId: string;
};

/**
 * Код счётчика по шаблону Яндекса: tag_ww.js (Вебвизор), init с referrer/url как в кабинете.
 * ID только из пропса (env). В App Router используем afterInteractive (официально без предупреждений ESLint); загрузка tag_ww.js async — как в коде Метрики.
 */
export function YandexMetrika({ counterId }: Props) {
  const id = counterId.trim();
  if (!/^\d{5,12}$/.test(id)) return null;

  const scriptSrc = `https://mc.webvisor.org/metrika/tag_ww.js?id=${encodeURIComponent(id)}`;

  return (
    <>
      <Script id="ym-tag-ww" strategy="afterInteractive">
        {`
(function(m,e,t,r,i,k,a){
  m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
  m[i].l=1*new Date();
  for (var j=0;j<document.scripts.length;j++){if(document.scripts[j].src===r){return;}}
  k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)
})(window,document,"script",${JSON.stringify(scriptSrc)},"ym");
ym(${JSON.stringify(id)},"init",{
  ssr:true,
  webvisor:true,
  trackHash:true,
  clickmap:true,
  ecommerce:"dataLayer",
  referrer:document.referrer,
  url:location.href,
  accurateTrackBounce:true,
  trackLinks:true
});
        `.trim()}
      </Script>
      <noscript>
        <div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={`https://mc.yandex.ru/watch/${encodeURIComponent(id)}`}
            style={{ position: "absolute", left: "-9999px" }}
            alt=""
            width={1}
            height={1}
          />
        </div>
      </noscript>
    </>
  );
}
