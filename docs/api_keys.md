# Getting API Keys

## Google AI Studio API Key
1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Sign in with your Google account.
3. Navigate to "API Keys" or "Get API Key" section.
4. Generate a new key (e.g., `AIzaSy...`).
5. Copy it into your `.env` file as `GOOGLE_API_KEY=your-key-here`.

## Hugging Face API Key
1. Visit [Hugging Face](https://huggingface.co/).
2. Log in or sign up.
3. Go to your profile > "Settings" > "Access Tokens".
4. Create a new token (e.g., Read or Write access).
5. Add to `.env` as `HF_API_KEY=your-token-here`.

## Setup
- Copy `.env.example` to `.env` and fill in your keys.
- Never commit `.env` to Git.cd doc