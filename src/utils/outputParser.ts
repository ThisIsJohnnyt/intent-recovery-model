interface ParsedOutput {
  narrative: string
  bullets: string[]
  actionItems: string[]
  rawOutput?: string
}

export function parseModelOutput(modelOutput: string): ParsedOutput {
  const narrative = extractSection(modelOutput, 'ORGANIZED NARRATIVE', 'KEY POINTS')
  const bullets = extractBulletPoints(
    extractSection(modelOutput, 'KEY POINTS', 'ACTION ITEMS')
  )
  const actionItems = extractBulletPoints(
    extractSection(modelOutput, 'ACTION ITEMS')
  )

  return {
    narrative: narrative.trim(),
    bullets: bullets.filter((b) => b.length > 0),
    actionItems: actionItems.filter((a) => a.length > 0 && a !== 'None identified.'),
    rawOutput: modelOutput,
  }
}

function extractSection(
  text: string,
  startMarker: string,
  endMarker?: string
): string {
  // Create regex patterns that handle various markdown formats
  const startPatterns = [
    new RegExp(`\\*\\*${startMarker}\\*\\*:?\\s*\\n([\\s\\S]*?)(?=\\*\\*${endMarker || '$'}|$)`, 'i'),
    new RegExp(`#{1,3}\\s+${startMarker}\\s*\\n([\\s\\S]*?)(?=#{1,3}|$)`, 'i'),
    new RegExp(`${startMarker}:?\\s*\\n([\\s\\S]*?)(?=\\*\\*|^#{1,3}|$)`, 'i'),
  ]

  for (const pattern of startPatterns) {
    const match = text.match(pattern)
    if (match && match[1]) {
      return match[1]
    }
  }

  // Fallback: if we can't find the exact section, return empty
  return ''
}

function extractBulletPoints(text: string): string[] {
  if (!text || text.trim().length === 0) {
    return []
  }

  // Split by common bullet markers
  const lines = text
    .split('\n')
    .map((line) => {
      // Remove markdown list markers
      return line
        .replace(/^[\s]*[-•*]\s+/, '') // Remove bullet markers
        .replace(/^[\s]*\d+\.\s+/, '') // Remove numbered list markers
        .replace(/^[\s]*\[\s*[xX]?\s*\]\s+/, '') // Remove checkboxes
        .trim()
    })
    .filter((line) => line.length > 0 && !line.startsWith('#'))

  return lines
}

export function formatForDisplay(output: ParsedOutput): string {
  let formatted = '**ORGANIZED NARRATIVE**\n'
  formatted += output.narrative + '\n\n'

  formatted += '**KEY POINTS**\n'
  output.bullets.forEach((bullet) => {
    formatted += `- ${bullet}\n`
  })

  formatted += '\n**ACTION ITEMS**\n'
  if (output.actionItems.length > 0) {
    output.actionItems.forEach((item) => {
      formatted += `- [ ] ${item}\n`
    })
  } else {
    formatted += 'None identified.\n'
  }

  return formatted
}
