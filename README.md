# Weekly YouTube Trends

A Python application that automatically tracks YouTube channels, summarizes their videos, and generates weekly content analysis using AI.

## Features

- Tracks multiple YouTube channels
- Gets video transcripts
- Generates AI summaries for each video using Claude
- Creates weekly channel content analysis
- Stores all data in Firebase

## Requirements

- Python 3.8+
- YouTube Data API key
- Anthropic API key (Claude)
- Firebase credentials

## Environment Variables

Create a `.env` file with:

```
YOUTUBE_API_KEY=your_youtube_api_key
ANTHROPIC_API_KEY=your_claude_api_key
FIREBASE_PROJECT_ID=your_project_id
GOOGLE_APPLICATION_CREDENTIALS=firebase-credentials.json
```

## Setup

1. Clone the repository
2. Install dependencies:

```
pip install -r requirements.txt
```

3. Add channels to Firebase:
   - Create a document in the `channels` collection for each channel you want to track
   - Use the channel ID as the document ID
   - Example: `channels/UC_mcI6nIlx5bp8QYJuxo7Rw`

## Usage

```
python main.py
```

## Data Structure

- `channels/`: Channel information and weekly summaries
- `videos/`: Individual video data and summaries

## Notes

- Channels are processed only once every 24 hours
- Only videos from the last 7 days are analyzed
- Transcripts are fetched in Portuguese or English
- All summaries are generated in Portuguese
