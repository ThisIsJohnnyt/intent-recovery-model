# 💭 ThoughtOrganizer

An AI-powered web application that helps people with ADHD, autism, and other neurodivergent conditions organize scattered, chaotic thoughts into clear, coherent notes.

## 🎯 Problem & Solution

Taking notes is hard—especially for neurodivergent individuals. Thoughts come in fragments, non-linearly, often with anxiety attached. Traditional note-taking apps just store these scattered thoughts as-is, which can trigger anxiety on re-reading.

**ThoughtOrganizer solves this**: It captures your messy input (voice or text) and uses AI to reorganize it into:
1. **Coherent Narrative** - Your thoughts rewritten clearly
2. **Key Points** - Extracted summaries
3. **Action Items** - Tasks and next steps highlighted

All processing happens on your device. No data leaves your browser.

## ✨ Features

- **Voice & Text Input**: Record thoughts or type them out—no need to organize as you go
- **On-Device AI**: Uses FLAN-T5 model running entirely in your browser (no server required)
- **Privacy First**: All data stays on your device—nothing is sent to external servers
- **Intelligent Chunking**: Automatically handles long notes by processing them intelligently
- **Supportive UX**: Progress indicators and encouraging messages during processing
- **Note History**: Save and revisit organized notes
- **Export Options**: Download notes as Markdown, JSON, or plain text
- **Dark Mode**: Built-in dark mode support

## 🏗️ Architecture

### Frontend
- **React 18** + **TypeScript** for type-safe UI
- **Vite** for fast development and optimized builds
- Responsive CSS with dark mode support

### AI/ML Pipeline
- **transformers.js** for in-browser LLM inference
- **FLAN-T5** (base or small) - lightweight text-to-text model
- Intelligent chunking for inputs exceeding token limits
- Real-time streaming output

### Storage
- **IndexedDB** for persistent, local-only storage
- Stores: raw input, organized outputs, audio recordings, metadata

## 🚀 Getting Started

### Prerequisites
- Node.js 16+ and npm/yarn
- Modern browser (Chrome, Firefox, Safari, Edge)

### Installation

```bash
# Install dependencies (skip scripts to avoid binary compilation issues)
npm install --ignore-scripts

# Start development server
npm run dev
```

The app will open at `http://localhost:5173`.

### Building for Production

```bash
npm run build
npm run preview
```

## 📖 How to Use

1. **Enter Your Thoughts**
   - Type scattered thoughts in the textarea, or
   - Click "Record Voice Note" to capture voice input

2. **Click "Organize My Thoughts"**
   - The AI processes your input on your device
   - You'll see supportive messages and progress indicators

3. **Review Organized Output**
   - Switch between three views: Narrative, Key Points, Action Items
   - Each view presents the same information differently

4. **Export or Save**
   - Export as Markdown/JSON, copy to clipboard, or save in history

5. **Review History**
   - Access previous organized notes anytime
   - Re-read in a calm, organized format

## 🧠 LLM Pipeline

### Processing Flow

```
User Input (voice/text)
  ↓
Input Preparation (normalize, estimate tokens)
  ↓
Conditional Routing:
  - If ≤6000 tokens: Single-pass processing
  - If >6000 tokens: Intelligent chunking → process → merge
  ↓
Single Comprehensive Pass:
  - One prompt requesting all three outputs
  - Real-time token streaming
  ↓
Output Parsing:
  - Regex-based extraction of sections
  - Narrative | Bullets | Actions
  ↓
Display & Storage:
  - Stream to UI with progress updates
  - Save to IndexedDB
```

### Prompt Strategy

The system uses a compassionate, supportive prompt that:
- Acknowledges the user's neurodivergence
- Asks for three specific, bounded outputs
- Preserves original meaning and tone
- Includes context from previous chunks (for multi-chunk processing)

### Model Selection

**Primary**: FLAN-T5 (base) - Good balance of quality and speed
- ~3.2GB quantized
- ~5-15s per single-pass inference
- Excellent at instruction following and text summarization

**Fallback**: FLAN-T5 (small) - Lighter if memory is constrained
- ~2.1GB quantized
- ~2-8s per inference

## 🎨 UX Features for Anxiety Reduction

- **Progress Indicators**: Shows chunk progress for long notes
- **Supportive Messages**: Rotating positive affirmations during processing
  - "Take a deep breath while I work. You're doing great."
  - "Relax—I'm handling the messy part for you."
  - And more...
- **Screen Reader Support**: All messages announced via aria-live
- **Visual Feedback**: Smooth animations, clear state changes
- **Accessibility**: Dark mode, readable typography, high contrast

## 📁 Project Structure

```
src/
├── components/
│   ├── InputPanel.tsx          # Voice + text input
│   ├── ProcessingView.tsx      # Progress + supportive messages
│   ├── OrganizedNotesView.tsx  # Three-tab output display
│   ├── HistoryPanel.tsx        # Saved notes timeline
│   └── App.tsx                 # Main app component
├── services/
│   ├── noteOrganizer.ts        # LLM pipeline orchestration
│   └── modelLoader.ts          # transformers.js setup
├── utils/
│   ├── outputParser.ts         # Section extraction
│   └── tokenization.ts         # Chunking logic
├── styles/
│   ├── *.css                   # Component styles
│   └── App.css                 # Layout styles
├── App.tsx
├── main.tsx
└── index.css
```

## 🔄 Data Flow

```
InputPanel (user input)
  ↓
App (state management)
  ↓
noteOrganizer.streamOrganizedNotes()
  ├── modelLoader.loadModel() → FLAN-T5
  ├── tokenization.intelligentChunk()
  ├── Single or Multi-pass processing
  └── outputParser.parseModelOutput()
  ↓
OrganizedNotesView (display tabs)
  ↓
App (save to IndexedDB)
  ↓
HistoryPanel (retrieve anytime)
```

## ⚡ Performance

- **Model Load**: ~10-30s first time (cached after)
- **Single-Pass**: 5-15s typical
- **Multi-Chunk**: 10-30s total (includes chunking + merge pass)
- **Memory**: ~2-4GB (FLAN-T5 quantized in browser)

## 🛠️ Tech Stack

| Category | Technology |
|----------|-----------|
| UI Framework | React 18 + TypeScript |
| Build Tool | Vite |
| AI/ML | transformers.js (ONNX) |
| Model | FLAN-T5 |
| Storage | IndexedDB |
| Styling | CSS3 (custom, no framework) |
| Voice | Web Speech API |

## 🧪 Browser Support

Tested and working on:
- Chrome 120+
- Firefox 121+
- Safari 17+
- Edge 120+

## 📝 Example Usage

### Input
```
worried about the project deadline tomorrow... also haven't slept well
should probably call mom haven't talked to her in a week
the budget spreadsheet needs updating before friday meeting
can't focus when I'm tired like this need coffee
```

### Organized Output

**Narrative**
> You're currently managing multiple concerns that are affecting your focus. There's an upcoming project deadline that's creating worry, compounded by poor sleep quality. Beyond work, you recognize the importance of maintaining your personal relationships—calling your mom—and staying on top of financial responsibilities through the budget update. You're aware that your current fatigue is impacting your productivity.

**Key Points**
- Project deadline is tomorrow and causing stress
- Poor sleep is affecting ability to focus
- Need to contact mother (overdue)
- Budget spreadsheet requires update before Friday meeting
- Physical state (fatigue, need for caffeine) is impacting productivity

**Action Items**
- [ ] Call mom
- [ ] Update budget spreadsheet before Friday
- [ ] Get more sleep tonight
- [ ] Handle project deadline tomorrow

## 🙏 Acknowledgments

Built with compassion for people with ADHD, autism, and other neurodivergent conditions who struggle with organizing scattered thoughts.

---

**Made with 💚 for people who think differently.**
