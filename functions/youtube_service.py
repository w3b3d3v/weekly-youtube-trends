from googleapiclient.discovery import build
from datetime import datetime, timedelta
from dateutil import parser
from config import YOUTUBE_API_KEY
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptAvailable, TranscriptsDisabled
from claude_service import ClaudeService
import requests
import re

class YouTubeService:
    def __init__(self, firebase_service):
        print("Inicializando serviço do YouTube...")
        self.youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        self.claude_service = ClaudeService(firebase_service)
        self.firebase_service = firebase_service

    def get_channel_info(self, channel_id):
        """Get channel information"""
        print(f"Buscando informações do canal: {channel_id}")
        request = self.youtube.channels().list(
            part="snippet,statistics",
            id=channel_id
        )
        response = request.execute()
        
        if not response['items']:
            print(f"❌ Canal não encontrado: {channel_id}")
            return None
            
        channel = response['items'][0]
        return {
            'id': channel['id'],
            'title': channel['snippet']['title'],
            'description': channel['snippet']['description'],
            'subscriber_count': channel['statistics']['subscriberCount'],
            'view_count': channel['statistics']['viewCount'],
            'video_count': channel['statistics']['videoCount']
        }

    def get_video_transcript(self, video_id):
        """Get video transcript using youtube-transcript.io API"""
        try:
            token = self.firebase_service.get_youtube_transcript_token()
            if not token:
                print("❌ Token de transcrição não encontrado")
                return {
                    'transcript': '',
                    'has_transcript': False
                }

            url = "https://www.youtube-transcript.io/api/transcripts"
            headers = {
                "authorization": f"{token}",
                "content-type": "application/json",
                "referer": f"https://www.youtube-transcript.io/videos/{video_id}"
            }
            data = {"ids": [video_id]}
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    # Get the first transcript's tracks
                    tracks = data[0].get('tracks', [])
                    if tracks and len(tracks) > 0:
                        # Get the first track's transcript
                        transcript = tracks[0].get('transcript', [])
                        if transcript:
                            # Combine all transcript pieces into one text
                            full_transcript = ' '.join([entry['text'] for entry in transcript])
                            
                            return {
                                'transcript': full_transcript,
                                'has_transcript': True
                            }
            
            print(f"❌ Transcrição não disponível para o vídeo {video_id}")
            return {
                'transcript': '',
                'has_transcript': False
            }
            
        except Exception as e:
            print(f"❌ Erro ao buscar transcrição para o vídeo {video_id}: {str(e)}")
            return {
                'transcript': '',
                'has_transcript': False
            }

    def get_recent_videos(self, channel_id):
        """Get videos published in the last 7 days"""
        seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat() + 'Z'
        print(f"Buscando vídeos desde: {seven_days_ago}")
        
        request = self.youtube.search().list(
            part="snippet",
            channelId=channel_id,
            maxResults=50,
            order="date",
            publishedAfter=seven_days_ago,
            type="video"
        )
        
        videos = []
        while request:
            response = request.execute()
            print(f"Encontrados {len(response['items'])} vídeos nesta página")
            
            for item in response['items']:
                video_data = {
                    'id': item['id']['videoId'],
                    'channel_id': channel_id,
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'published_at': item['snippet']['publishedAt'],
                    'thumbnail_url': item['snippet']['thumbnails']['high']['url']
                }
                
                # Get additional video statistics
                print(f"Buscando estatísticas para o vídeo: {video_data['title']}")
                video_stats = self.get_video_statistics(video_data['id'])
                video_data.update(video_stats)
                
                # Get video transcript
                print(f"Buscando transcrição para o vídeo: {video_data['title']}")
                transcript_data = self.get_video_transcript(video_data['id'])
                video_data.update(transcript_data)
                
                # Generate summary if transcript is available
                if video_data['has_transcript']:
                    print(f"Gerando resumo para o vídeo: {video_data['title']}")
                    summary_data = self.claude_service.summarize_transcript(
                        video_data['transcript'],
                        video_data['title']
                    )
                    video_data.update(summary_data)
                else:
                    video_data.update({
                        'summary': '',
                        'has_summary': False
                    })
                
                videos.append(video_data)
            
            request = self.youtube.search().list_next(request, response)
            
        # After processing all videos, create a weekly channel summary
        if videos:
            print(f"Gerando resumo semanal para o canal...")
            channel_info = self.get_channel_info(channel_id)
            if channel_info:
                weekly_summary = self.claude_service.create_weekly_channel_summary(
                    channel_info['title'],
                    videos
                )
                # Update channel info with weekly summary
                channel_info.update(weekly_summary)
                return videos, channel_info
            
        return videos, None

    def get_video_statistics(self, video_id):
        """Get video statistics"""
        request = self.youtube.videos().list(
            part="statistics",
            id=video_id
        )
        response = request.execute()
        
        if not response['items']:
            print(f"❌ Estatísticas não encontradas para o vídeo: {video_id}")
            return {}
            
        stats = response['items'][0]['statistics']
        return {
            'view_count': stats.get('viewCount', 0),
            'like_count': stats.get('likeCount', 0),
            'comment_count': stats.get('commentCount', 0)
        }

    def extract_channel_id_from_url(self, url):
        """Extract channel ID from a YouTube channel URL
        
        Supports URLs in formats:
        - youtube.com/channel/UC... (channel ID)
        - youtube.com/c/... (custom URL)
        - youtube.com/@... (handle)
        """
        try:
            response = requests.get(url)
            if response.status_code != 200:
                print(f"❌ Erro ao acessar URL: {url}")
                return None

            # First try to find channel ID in URL
            channel_id_match = re.search(r'youtube\.com/channel/(UC[\w-]+)', url)
            if channel_id_match:
                return channel_id_match.group(1)

            html_content = response.text
            
            # Try to find channel ID in RSS feed URL
            rss_match = re.search(r'channel_id=(UC[\w-]+)', html_content)
            if rss_match:
                return rss_match.group(1)

            # If not found in RSS, try the channelId in meta data
            channel_id_match = re.search(r'"channelId":"(UC[\w-]+)"', html_content)
            if channel_id_match:
                return channel_id_match.group(1)
            
            print(f"❌ Não foi possível encontrar o ID do canal na URL: {url}")
            return None

        except Exception as e:
            print(f"❌ Erro ao processar URL do canal: {str(e)}")
            return None 