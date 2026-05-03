import { intentNav } from "@/data/texts/intent-sections";

export function IntentNavSection() {
  return (
    <nav
      className="sticky top-0 z-30 border-b border-[var(--cool-border)] bg-[color-mix(in_srgb,white_92%,var(--main-bg))]/95 shadow-sm backdrop-blur-md supports-[backdrop-filter]:bg-[color-mix(in_srgb,white_88%,var(--main-bg))]/90"
      aria-label={intentNav.ariaLabel}
    >
      <div className="mx-auto max-w-6xl px-4 py-2.5 min-[360px]:px-5 sm:px-6 lg:px-8">
        <ul className="flex flex-wrap items-center justify-center gap-x-1 gap-y-1 sm:justify-start sm:gap-x-0 sm:gap-y-2">
          {intentNav.links.map((link, i) => (
            <li key={link.href} className="flex items-center">
              {i > 0 ? (
                <span
                  className="mx-1 hidden h-3 w-px bg-[var(--cool-border)] sm:mx-2 sm:inline"
                  aria-hidden
                />
              ) : null}
              <a
                href={link.href}
                className="whitespace-nowrap rounded-lg px-2.5 py-1.5 text-[11px] font-medium text-[var(--deep-blue)] transition-colors hover:bg-[color-mix(in_srgb,var(--soft-blue-bg)_80%,white)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--deep-blue)_30%,transparent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--main-bg)] sm:px-3 sm:text-xs"
              >
                {link.label}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
}
