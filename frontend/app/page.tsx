export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] px-4 text-center">
      <h1 className="text-4xl font-bold text-[#1B3A6B] mb-4">Git for News</h1>
      <p className="text-lg text-gray-600 max-w-xl mb-8">
        Paste a news URL or topic — StoryTrace tracks how the story mutated across
        countries and outlets, visualized as a drift tree.
      </p>
      <p className="text-sm text-gray-400">Analysis coming in PR-17</p>
    </div>
  )
}
