import { loadModel } from './modelLoader'
import { parseModelOutput } from '../utils/outputParser'
import { intelligentChunk, estimateTokens } from '../utils/tokenization'

const SYSTEM_PROMPT = `You are a compassionate AI assistant helping someone with ADHD/autism organize their scattered thoughts.

The user has provided messy, non-linear thoughts below. Your job is to transform them into three clear, organized views that reduce anxiety and improve clarity.`

const USER_PROMPT_TEMPLATE = `Please provide:

1. **ORGANIZED NARRATIVE**: Rewrite the thoughts as a coherent, flowing narrative. Group related ideas. Keep the original meaning and tone. Make it less anxiety-inducing to read.

2. **KEY POINTS**: Extract 3-7 key ideas as clear, simple bullet points.

3. **ACTION ITEMS**: Extract any tasks, next steps, or things to do. If none, write "None identified."

Format your response exactly as shown above with those three sections clearly labeled.`

interface OrganizedNote {
  narrative: string
  bullets: string[]
  actionItems: string[]
  rawOutput?: string
}

export async function* streamOrganizedNotes(
  rawInput: string,
  onProgress: (progress: number, message: string) => void
): AsyncGenerator<OrganizedNote> {
  try {
    const model = await loadModel()
    onProgress(10, 'Model loaded. Analyzing your thoughts...')

    // Estimate tokens
    const inputTokens = estimateTokens(rawInput)
    const maxInputTokens = 6000

    if (inputTokens <= maxInputTokens) {
      // Single pass processing
      onProgress(20, 'Organizing your thoughts into clarity...')
      yield* processSinglePass(model, rawInput, onProgress)
    } else {
      // Multi-chunk processing
      onProgress(20, 'Your thoughts are quite detailed. Processing in sections...')
      yield* processMultiChunk(model, rawInput, onProgress)
    }
  } catch (err) {
    console.error('Error in streamOrganizedNotes:', err)
    throw err
  }
}

async function* processSinglePass(
  model: any,
  input: string,
  onProgress: (progress: number, message: string) => void
): AsyncGenerator<OrganizedNote> {
  onProgress(30, 'Generating organized narrative...')

  const prompt = `${SYSTEM_PROMPT}\n\nUSER'S RAW THOUGHTS:\n${input}\n\n${USER_PROMPT_TEMPLATE}`

  let fullOutput = ''
  let tokenCount = 0

  try {
    for await (const chunk of model.stream(prompt)) {
      fullOutput += chunk
      tokenCount++

      // Update progress (simulate streaming)
      const progress = 30 + Math.min((tokenCount / 100) * 60, 60)
      onProgress(progress, 'Processing...')

      // Try to parse incremental output
      try {
        const parsed = parseModelOutput(fullOutput)
        yield parsed
      } catch {
        // Incomplete output, keep collecting
      }
    }

    onProgress(95, 'Finalizing your organized thoughts...')

    // Final parse
    const finalOutput = parseModelOutput(fullOutput)
    finalOutput.rawOutput = fullOutput
    yield finalOutput

    onProgress(100, 'Done! Your thoughts are organized.')
  } catch (err) {
    console.error('Error in processSinglePass:', err)
    throw err
  }
}

async function* processMultiChunk(
  model: any,
  input: string,
  onProgress: (progress: number, message: string) => void
): AsyncGenerator<OrganizedNote> {
  try {
    // Split input into chunks
    const chunks = intelligentChunk(input)
    onProgress(
      25,
      `Split into ${chunks.length} sections. Processing section 1...`
    )

    const outputs: string[] = []

    // Process each chunk
    for (let i = 0; i < chunks.length; i++) {
      const chunkNumber = i + 1
      const chunk = chunks[i]

      // Add context header for later chunks
      let contextPrefix = ''
      if (i > 0 && outputs.length > 0) {
        // Extract brief summary from previous chunk for context
        const prevSummary = outputs[i - 1].substring(0, 100) + '...'
        contextPrefix = `[Context from previous section: ${prevSummary}]\n\n`
      }

      const prompt = `${SYSTEM_PROMPT}\n\nUSER'S RAW THOUGHTS (Section ${chunkNumber}/${chunks.length}):\n${contextPrefix}${chunk}\n\n${USER_PROMPT_TEMPLATE}`

      onProgress(
        25 + (i / chunks.length) * 60,
        `Processing section ${chunkNumber} of ${chunks.length}...`
      )

      let chunkOutput = ''

      for await (const token of model.stream(prompt)) {
        chunkOutput += token
      }

      outputs.push(chunkOutput)

      // Yield incremental result
      try {
        const parsed = parseModelOutput(chunkOutput)
        yield parsed
      } catch {
        // Continue collecting
      }
    }

    // Merge pass: combine all outputs into coherent narrative
    onProgress(90, 'Combining sections into coherent narrative...')

    const mergePrompt = `You are organizing scattered thoughts. Here are multiple processed sections that came from a single raw input.

Please create ONE unified organized output that combines all these sections coherently:

${outputs.map((out, idx) => `SECTION ${idx + 1}:\n${out}`).join('\n\n---\n\n')}

Please provide the FINAL UNIFIED OUTPUT using the same format:

1. **ORGANIZED NARRATIVE**: Single coherent narrative combining all sections
2. **KEY POINTS**: Consolidated key points from all sections (remove duplicates)
3. **ACTION ITEMS**: All action items from all sections

Format your response clearly with these exact section labels.`

    let mergedOutput = ''
    for await (const token of model.stream(mergePrompt)) {
      mergedOutput += token
    }

    onProgress(98, 'Finalizing your organized thoughts...')

    const finalOutput = parseModelOutput(mergedOutput)
    finalOutput.rawOutput = mergedOutput
    yield finalOutput

    onProgress(100, 'Done! Your thoughts are organized.')
  } catch (err) {
    console.error('Error in processMultiChunk:', err)
    throw err
  }
}
