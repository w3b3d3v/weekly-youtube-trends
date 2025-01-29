from googleapiclient.discovery import build
from datetime import datetime, timedelta
from dateutil import parser
from config import YOUTUBE_API_KEY

class YouTubeService:
    def __init__(self):
        print("Inicializando serviço do YouTube...")
        self.youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

    def get_channel_info(self, channel_id):
        """Get channel information"""
        print(f"Buscando informações do canal: {channel_id}")
        request = self.youtube.channels().list(
            part="snippet,statistics",
            id=channel_id
        )
        response = request.execute()
        print("response: ", response)
        
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
                
                videos.append(video_data)
            
            request = self.youtube.search().list_next(request, response)
            
        return videos

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