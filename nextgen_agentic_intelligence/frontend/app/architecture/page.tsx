import Header from "@/components/Header";
import ObjectiveBanner from "@/components/architecture/ObjectiveBanner";
import AgentUseCases from "@/components/architecture/AgentUseCases";
import FlowCanvas from "@/components/architecture/FlowCanvas";

export const metadata = {
  title: "Architecture · NextGen Agentic Intelligence",
};

export default function ArchitecturePage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-white to-uhc-blue-soft/40">
      <Header />
      <div className="mx-auto max-w-[1400px] space-y-10 px-4 py-8 sm:px-6">
        <ObjectiveBanner />
        <AgentUseCases />
        <section>
          <div className="mb-3">
            <h2 className="text-[18px] font-bold tracking-tight text-uhc-blue">How it works — the agentic flow</h2>
            <p className="text-[13px] text-gray-500">
              From a question to a validated signal and back. Press play, hover a node, or click for details.
            </p>
          </div>
          <FlowCanvas />
        </section>
      </div>
    </main>
  );
}
