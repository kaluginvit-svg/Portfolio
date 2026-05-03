import { ImageResponse } from "next/og";
import { siteMetadata } from "@/data/seo/site-metadata";

export const runtime = "edge";

export const alt = "Выплаты семьям погибших участников СВО — предварительный расчёт";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          height: "100%",
          width: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: 64,
          background: "linear-gradient(135deg, #0b1f3a 0%, #163a63 55%, #0b1f3a 100%)",
          color: "#f8fafc",
          fontFamily:
            'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: 16, maxWidth: 900 }}>
          <p
            style={{
              fontSize: 28,
              fontWeight: 600,
              letterSpacing: "0.04em",
              textTransform: "uppercase",
              color: "rgba(248,250,252,0.75)",
              margin: 0,
            }}
          >
            {siteMetadata.openGraphSiteName}
          </p>
          <h1
            style={{
              fontSize: 52,
              fontWeight: 700,
              lineHeight: 1.15,
              margin: 0,
            }}
          >
            Выплаты семьям погибших участников СВО
          </h1>
          <p
            style={{
              fontSize: 28,
              lineHeight: 1.35,
              color: "rgba(248,250,252,0.88)",
              margin: 0,
            }}
          >
            Предварительный расчёт, документы и разбор заявлений
          </p>
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            fontSize: 22,
            color: "rgba(248,250,252,0.7)",
          }}
        >
          <span
            style={{
              width: 48,
              height: 4,
              borderRadius: 2,
              background: "linear-gradient(90deg, #b3262e, #163a63)",
            }}
          />
          Ориентир по сумме и маршруту подачи
        </div>
      </div>
    ),
    { ...size },
  );
}
