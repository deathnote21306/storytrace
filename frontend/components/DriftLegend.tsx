export default function DriftLegend() {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500 mt-2">
      <span className="font-semibold">Drift score:</span>
      <span className="flex items-center gap-1.5">
        <span className="w-3 h-3 rounded-full bg-[#27A06A] inline-block" />
        Low (0–33)
      </span>
      <span className="flex items-center gap-1.5">
        <span className="w-3 h-3 rounded-full bg-[#F59E0B] inline-block" />
        Mid (34–66)
      </span>
      <span className="flex items-center gap-1.5">
        <span className="w-3 h-3 rounded-full bg-[#E8562A] inline-block" />
        High (67–100)
      </span>
    </div>
  )
}
