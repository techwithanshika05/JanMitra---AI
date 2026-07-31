import { Fragment } from 'react'

const cleanText = value => String(value || '')
  .replace(/```[\w-]*\n?/g, '')
  .replace(/```/g, '')
  .replace(/[\u200B-\u200D\uFEFF]/g, '')
  .replace(/\r\n?/g, '\n')
  .trim()

function InlineText({ children }) {
  const text = String(children || '')
    .replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, '$1 — $2')
    .replace(/`([^`]+)`/g, '$1')
  const parts = text.split(/(\*\*[^*]+\*\*)/g)

  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={index} className="font-extrabold text-[#172033] dark:text-white">{part.slice(2, -2)}</strong>
    }
    return <Fragment key={index}>{part.replace(/\*/g, '')}</Fragment>
  })
}

export default function ChatResponse({ content }) {
  const lines = cleanText(content).split('\n')
  const blocks = []
  let list = []
  let listType = null

  const flushList = () => {
    if (!list.length) return
    const Tag = listType === 'ordered' ? 'ol' : 'ul'
    blocks.push(
      <Tag
        key={`list-${blocks.length}`}
        className={`${listType === 'ordered' ? 'list-decimal' : 'list-disc'} ml-5 space-y-2 marker:text-[#0d7c66]`}
      >
        {list.map((item, index) => <li key={index} className="pl-1"><InlineText>{item}</InlineText></li>)}
      </Tag>
    )
    list = []
    listType = null
  }

  lines.forEach((rawLine, index) => {
    const line = rawLine.trim()
    if (!line) {
      flushList()
      return
    }

    const heading = line.match(/^#{1,6}\s+(.+)$/)
    const bullet = line.match(/^[-*•]\s+(.+)$/)
    const numbered = line.match(/^\d+[.)]\s+(.+)$/)

    if (bullet || numbered) {
      const nextType = numbered ? 'ordered' : 'unordered'
      if (list.length && listType !== nextType) flushList()
      listType = nextType
      list.push((bullet || numbered)[1])
      return
    }

    flushList()
    if (heading) {
      blocks.push(
        <h3 key={`heading-${index}`} className="pt-1 text-base font-extrabold text-[#172033] dark:text-white">
          <InlineText>{heading[1]}</InlineText>
        </h3>
      )
    } else {
      blocks.push(
        <p key={`paragraph-${index}`} className="leading-7">
          <InlineText>{line}</InlineText>
        </p>
      )
    }
  })
  flushList()

  return <div className="space-y-3 break-words">{blocks}</div>
}
