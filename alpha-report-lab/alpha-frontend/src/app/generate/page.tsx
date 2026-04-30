import GenerateForm from "@/components/generate/GenerateForm";

export default function GeneratePage() {
  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight">Generate Alpha Report</h1>
        <p className="text-gray-500 mt-1 text-sm">
          Configure the inputs and our multi-agent system will produce a full research report.
        </p>
      </div>
      <GenerateForm />
    </div>
  );
}
