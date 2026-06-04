/* Co-branded top bar: UnitedHealthcare (primary) + NextGen Agentic Intelligence
 * product name + "powered by Optum". Blue with an Optum-orange accent rule. */
const SERIF = 'Georgia, "Times New Roman", serif';
const ROUNDED = '"Arial Rounded MT Bold", "Helvetica Rounded", ui-rounded, system-ui, sans-serif';

export default function Header() {
  return (
    <header className="w-full border-b border-uhc-blue-soft bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-5 py-2.5">
        {/* Primary brand: UnitedHealthcare */}
        <div className="flex items-center gap-2.5">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/uhc-mark.svg" alt="UnitedHealthcare" className="h-9 w-auto" />
          <div className="leading-[1.05]" style={{ fontFamily: SERIF }}>
            <div className="text-[15px] font-semibold text-uhc-blue">United</div>
            <div className="text-[15px] font-semibold text-uhc-blue">Healthcare</div>
          </div>
        </div>

        {/* Product name */}
        <div className="hidden text-center sm:block">
          <div className="text-[15px] font-bold tracking-tight text-uhc-blue">
            NextGen Agentic Intelligence
          </div>
          <div className="text-[10px] uppercase tracking-[0.18em] text-gray-400">Supervisor · Multi-Agent</div>
        </div>

        {/* Powered by Optum */}
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-gray-400">powered by</span>
          <span
            className="text-[19px] font-extrabold leading-none text-optum-orange"
            style={{ fontFamily: ROUNDED }}
          >
            Optum
          </span>
        </div>
      </div>
      {/* Optum-orange accent rule */}
      <div className="h-1 w-full bg-gradient-to-r from-uhc-blue via-uhc-blue-bright to-optum-orange" />
    </header>
  );
}
