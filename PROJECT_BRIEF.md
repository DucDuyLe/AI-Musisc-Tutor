# PROJECT-BASED INTERVIEW CHALLENGE: AI-Powered Music Theory Tutor

## Project Title: Smart Music-Theory Tutor (AI + Notation + Audio)
**Duration:** 7 Days (Solo Project)

## 🌟 OVERVIEW
We're assembling a resilient, passionate, and creative team of future innovators. If you're passionate about music, AI, and full-stack building, this is your chance to stand out.

We're building a next-gen music learning platform that quizzes students on AMEB-style (AMEB = Australian Music Examination Board) theory and performance. So far, we only support text-based MCQs.

Now we want to explore AI-generated questions that include:
- Musical notation (rendered as images)
- Audio clips (the student can hear or replay)
- Explanations to aid understanding

This challenge is part of our interview process. We are not looking for perfection. We care about:
- Creative thinking
- Willpower and follow-through
- Comfort working with full-stack and AI
- Accuracy aligned with the AMEB syllabus

## 🔧 YOUR TASK
Build a mini web-app that generates and displays music-theory questions.

Your app should:
- Let users choose an instrument and grade level (hardcode a few for demo purposes)
- On clicking "Generate Question":
  - Call an AI agent to generate a theory MCQ (concepts can be randomized)
  - Generate a corresponding notation image
  - Generate a playable audio clip of the phrase
  - Return an explanation of the correct answer
- Show all the above in a simple front-end
- Let the user select an answer and then show the correct answer + explanation

### API Guidelines
Your API should accept:
```json
{
  "instrument": "<string>",
  "grade": <int>
}
```

The response should include:
```json
{
  "notation_image_base64": "...",
  "audio_url": "...",
  "explanation": "...",
  "question": "...",
  "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
  "correct": "B"
}
```

Ensure all generated content is musically accurate and reflects the AMEB syllabus as closely as possible.

## 💻 TECH REQUIREMENTS
- You can use any stack you prefer
- You can use any AI/LLM setup (OpenAI, Claude, local models, etc.)
- The AI pipeline must be fully automated — no manual edits
- Outputs must be factually sound and relevant for the given instrument + grade

## 📋 DELIVERABLES
1. Working demo (local or deployed — either is fine)
2. GitHub Repo with code
3. Brief description of architecture and setup (can be inline in README)
4. README with setup/run instructions
5. (Optional but nice) Quick walkthrough video (max 3 mins)

## 🎯 EVALUATION PHILOSOPHY
This is not a competition. We're not here to nitpick or score points. We're simply looking to understand:
- How you approach problems
- How you execute ideas
- How well you understand AI and full-stack dev
- Your attention to detail and musical correctness

We value experimentation and creativity more than rigid correctness. Feel free to interpret the brief in your own style.

## ✨ BONUS IDEAS (Totally Optional)
- Let students play via microphone to match pitch
- Use adaptive difficulty based on responses
- Save results to DB and show progress

## 🔍 WHAT HAPPENS NEXT
We'll explore your project, read your code, and get a feel for your creative process. If we're impressed, we'll invite you to a final chat to discuss your thinking, your build style, and your ideas.

**NOTE:** You are not expected to ship a perfect or polished product. We care more about how you think and build under time constraints.

We're genuinely excited to see what you come up with. Have fun and go wild! 