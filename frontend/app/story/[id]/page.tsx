export default async function StoryPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  return (
    <div className="flex items-center justify-center min-h-[80vh] text-gray-400">
      Story view for {id} — coming in PR-15 / PR-17
    </div>
  )
}
