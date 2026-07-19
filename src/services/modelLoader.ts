import { pipeline, env } from '@xenova/transformers'

// Set up transformers.js environment
env.allowLocalModels = false
env.allowRemoteModels = true
env.localModelPath = 'https://huggingface.co/'

let cachedModel: any = null
let modelLoadingPromise: Promise<any> | null = null

export async function loadModel(): Promise<any> {
  // Return cached model if available
  if (cachedModel) {
    return cachedModel
  }

  // If already loading, wait for the existing promise
  if (modelLoadingPromise) {
    return modelLoadingPromise
  }

  // Start loading the model
  modelLoadingPromise = loadModelInternal()
  return modelLoadingPromise
}

async function loadModelInternal(): Promise<any> {
  try {
    console.log('Loading text-to-text generation model...')

    // Use a smaller, quantized model that works well in-browser
    // FLAN-T5 is reliable for text organization and summarization
    const model = await pipeline(
      'text2text-generation',
      'Xenova/flan-t5-base',
      {
        quantized: true,
      }
    )

    console.log('Model loaded successfully')
    cachedModel = model
    return model
  } catch (err) {
    console.error('Failed to load primary model:', err)

    // Fallback to an even smaller model
    try {
      console.log('Falling back to smaller model...')
      const fallbackModel = await pipeline(
        'text2text-generation',
        'Xenova/flan-t5-small',
        {
          quantized: true,
        }
      )
      console.log('Fallback model loaded')
      cachedModel = fallbackModel
      return fallbackModel
    } catch (fallbackErr) {
      console.error('Fallback model also failed:', fallbackErr)
      throw new Error('Failed to load any text generation model')
    }
  }
}

export function clearModel(): void {
  cachedModel = null
  modelLoadingPromise = null
}

export async function streamFromModel(
  model: any,
  prompt: string
): Promise<AsyncGenerator<string>> {
  return model.tokenizer.encode(prompt)
}
