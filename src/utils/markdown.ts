function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function formatInline(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code class="md-inline-code">$1</code>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
}

function isTableRow(line: string): boolean {
  const trimmed = line.trim()
  return trimmed.startsWith('|') && trimmed.endsWith('|') && trimmed.length > 2
}

function isTableSeparator(line: string): boolean {
  const cells = parseTableRow(line)
  if (!cells.length) return false
  return cells.every((cell) => /^:?-{3,}:?$/.test(cell))
}

function parseTableRow(line: string): string[] {
  return line
    .trim()
    .replace(/^\|/, '')
    .replace(/\|$/, '')
    .split('|')
    .map((cell) => cell.trim())
}

function parseSeparatorAlignments(line: string): Array<'left' | 'center' | 'right' | null> {
  return parseTableRow(line).map((cell) => {
    const left = cell.startsWith(':')
    const right = cell.endsWith(':')
    if (left && right) return 'center'
    if (right) return 'right'
    if (left) return 'left'
    return null
  })
}

function renderTableHtml(headerLine: string, separatorLine: string, bodyLines: string[]): string {
  const headers = parseTableRow(headerLine)
  const alignments = parseSeparatorAlignments(separatorLine)
  const rows = bodyLines.map(parseTableRow)

  const thead = headers
    .map((cell, index) => {
      const align = alignments[index]
      const style = align ? ` style="text-align:${align}"` : ''
      return `<th${style}>${formatInline(escapeHtml(cell))}</th>`
    })
    .join('')

  const tbody = rows
    .map((row) => {
      const cells = headers
        .map((_, index) => {
          const align = alignments[index]
          const style = align ? ` style="text-align:${align}"` : ''
          const value = row[index] ?? ''
          return `<td${style}>${formatInline(escapeHtml(value))}</td>`
        })
        .join('')
      return `<tr>${cells}</tr>`
    })
    .join('')

  return `<table class="md-table"><thead><tr>${thead}</tr></thead><tbody>${tbody}</tbody></table>`
}

function extractTables(source: string): { text: string; tables: string[] } {
  const lines = source.split('\n')
  const tables: string[] = []
  const output: string[] = []
  let index = 0

  while (index < lines.length) {
    const current = lines[index] ?? ''
    const next = lines[index + 1] ?? ''

    if (isTableRow(current) && isTableSeparator(next)) {
      const bodyLines: string[] = []
      index += 2
      while (index < lines.length && isTableRow(lines[index] ?? '')) {
        bodyLines.push(lines[index] ?? '')
        index += 1
      }
      const tableIndex = tables.length
      tables.push(renderTableHtml(current, next, bodyLines))
      output.push(`@@TABLE_${tableIndex}@@`)
      continue
    }

    output.push(current)
    index += 1
  }

  return { text: output.join('\n'), tables }
}

export function renderMarkdown(source: string): string {
  if (!source.trim()) return ''

  const codeBlocks: string[] = []
  let text = source.replace(/```([\s\S]*?)```/g, (_, code: string) => {
    const index = codeBlocks.length
    codeBlocks.push(`<pre class="md-pre"><code>${escapeHtml(code.trim())}</code></pre>`)
    return `@@CODE_BLOCK_${index}@@`
  })

  const { text: textWithoutTables, tables } = extractTables(text)
  text = escapeHtml(textWithoutTables)

  text = text
    .replace(/^###### (.+)$/gm, '<h6>$1</h6>')
    .replace(/^##### (.+)$/gm, '<h5>$1</h5>')
    .replace(/^#### (.+)$/gm, '<h4>$1</h4>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code class="md-inline-code">$1</code>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>\n?)+/g, (match) => `<ul>${match}</ul>`)
    .replace(/\n{2,}/g, '</p><p>')
    .replace(/\n/g, '<br />')

  text = `<p>${text}</p>`.replace(/<p><\/p>/g, '')

  tables.forEach((table, tableIndex) => {
    text = text.replace(`@@TABLE_${tableIndex}@@`, table)
  })

  codeBlocks.forEach((block, blockIndex) => {
    text = text.replace(`@@CODE_BLOCK_${blockIndex}@@`, block)
  })

  return text
}

export function markdownExcerpt(source: string, maxLength = 120): string {
  const plain = source
    .replace(/```[\s\S]*?```/g, '')
    .replace(/[#>*`[\]()\-|]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
  if (plain.length <= maxLength) return plain
  return `${plain.slice(0, maxLength)}…`
}
