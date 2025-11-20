# Environment Setup Instructions

## Setting up API Keys

This project requires OpenAI API keys to function properly. Follow these steps:

### 1. Create Environment Files

Copy the example files and add your actual API keys:

```bash
# Copy main environment file
cp .env.example .env

# Copy API environment file  
cp api/.env.example api/.env
```

### 2. Add Your OpenAI API Key

Edit both `.env` files and replace `your_openai_api_key_here` with your actual OpenAI API key:

**In `.env`:**
```bash
LLM_API_KEY=sk-proj-your-actual-api-key-here
OPENAI_API_KEY=sk-proj-your-actual-api-key-here
```

**In `api/.env`:**
```bash
LLM_API_KEY=sk-proj-your-actual-api-key-here
OPENAI_API_KEY=sk-proj-your-actual-api-key-here
```

### 3. Get Your OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/account/api-keys)
2. Sign in to your account
3. Click "Create new secret key"
4. Copy the generated key and use it in your environment files

### 4. Security Note

- **Never commit your actual API keys to Git**
- The `.env` files are included in `.gitignore` to prevent accidental commits
- Only the `.env.example` files should be committed to the repository

### 5. Verify Setup

After setting up your API keys, restart the server:

```bash
python rag_server.py
```

You should see: `INFO:__main__:OpenAI client initialized` in the logs, confirming your API key is working.