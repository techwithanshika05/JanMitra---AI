import { Sparkles } from 'lucide-react'

export default function LoadingScreen({ visible }) {
  if (!visible) return null

  return (
    <div className="fixed inset-0 z-[99999] flex flex-col items-center justify-center gap-7 bg-[#101c17] text-white transition-opacity duration-600">
      <div className="relative w-[100px] h-[100px] grid place-items-center">
        <div className="absolute inset-0 border-2 border-white/15 border-t-[#ff7a45] border-r-[#43d9b4] rounded-full animate-spin-slow"></div>
        <div className="w-[70px] h-[70px] grid place-items-center rounded-[24px] bg-[#f4c95d] text-[#102019] shadow-[0_15px_45px_rgba(244,201,93,0.25)] animate-pulse-soft">
          <Sparkles size={30} />
        </div>
      </div>
      <div className="text-center">
        <div className="font-heading text-[36px] font-extrabold tracking-[-1.8px]">
          JanMitra <span className="text-[#54d9b7]">AI</span>
        </div>
        <p className="mt-1 text-white/55 text-sm">Your Citizen Welfare Assistant</p>
      </div>
    </div>
  )
}