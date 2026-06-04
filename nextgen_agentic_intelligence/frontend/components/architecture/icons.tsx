/* Inline-SVG icon set for the architecture diagram. Feather/Lucide-style 24x24
 * line icons (fill=none, stroke=currentColor) to match the existing inline SVGs
 * in MessageBubble.tsx. Color is inherited from the parent via currentColor. */
import type { IconName } from "@/lib/architecture";

type IconProps = { name: IconName; className?: string; size?: number };

const PATHS: Record<IconName, JSX.Element> = {
  database: (
    <>
      <ellipse cx="12" cy="5" rx="9" ry="3" />
      <path d="M3 5v14a9 3 0 0 0 18 0V5" />
      <path d="M3 12a9 3 0 0 0 18 0" />
    </>
  ),
  layers: (
    <>
      <polygon points="12 2 2 7 12 12 22 7 12 2" />
      <polyline points="2 17 12 22 22 17" />
      <polyline points="2 12 12 17 22 12" />
    </>
  ),
  memory: (
    <>
      <rect x="6" y="6" width="12" height="12" rx="2" />
      <path d="M9 1v4M15 1v4M9 19v4M15 19v4M1 9h4M1 15h4M19 9h4M19 15h4" />
      <rect x="10" y="10" width="4" height="4" rx="1" />
    </>
  ),
  agent: (
    <>
      <rect x="5" y="8" width="14" height="11" rx="2" />
      <path d="M12 8V4M12 4h-1.5a1.5 1.5 0 1 1 1.5-1.5V4z" />
      <circle cx="9" cy="13" r="1" />
      <circle cx="15" cy="13" r="1" />
      <path d="M9 16h6" />
      <path d="M2 12v3M22 12v3" />
    </>
  ),
  signal: (
    <>
      <path d="M3 17l5-5 4 3 8-9" />
      <path d="M16 6h5v5" />
    </>
  ),
  search: (
    <>
      <circle cx="11" cy="11" r="7" />
      <path d="M21 21l-4.3-4.3" />
    </>
  ),
  tool: (
    <>
      <path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18v3h3l6.3-6.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.1-.4-.4-2.1z" />
    </>
  ),
  sql: (
    <>
      <ellipse cx="12" cy="6" rx="8" ry="3" />
      <path d="M4 6v12a8 3 0 0 0 16 0V6" />
      <path d="M9 13l-2 2 2 2M15 13l2 2-2 2" />
    </>
  ),
  report: (
    <>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <path d="M8 13h8M8 17h6M8 9h2" />
    </>
  ),
  shield: (
    <>
      <path d="M12 2l8 3v6c0 5-3.5 8-8 11-4.5-3-8-6-8-11V5z" />
      <path d="M9 12l2 2 4-4" />
    </>
  ),
  cms: (
    <>
      <path d="M3 21h18" />
      <path d="M5 21V8l7-5 7 5v13" />
      <path d="M9 21v-6h6v6" />
      <path d="M9 11h.01M15 11h.01" />
    </>
  ),
  embedding: (
    <>
      <circle cx="6" cy="6" r="2" />
      <circle cx="18" cy="6" r="2" />
      <circle cx="6" cy="18" r="2" />
      <circle cx="18" cy="18" r="2" />
      <circle cx="12" cy="12" r="2.4" />
      <path d="M7.7 7.7l2.6 2.6M16.3 7.7l-2.6 2.6M7.7 16.3l2.6-2.6M16.3 16.3l-2.6-2.6" />
    </>
  ),
};

export default function Icon({ name, className, size = 18 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      {PATHS[name]}
    </svg>
  );
}
