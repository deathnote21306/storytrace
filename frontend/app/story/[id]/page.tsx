export default function StoryPage({ params }: { params: { id: string } }) {
  return (
    <div className="flex items-center justify-center min-h-[80vh] text-gray-400">
      Story view for {params.id} — coming in PR-15 / PR-17
    </div>
  )
}
