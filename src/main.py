from firebase_service import FirebaseService
from youtube_service import YouTubeService
import time

def main():
    print("Iniciando o processo de atualização...")
    firebase_service = FirebaseService()
    youtube_service = YouTubeService()
    
    # Get all channels from Firebase
    print("Buscando canais do Firebase...")
    channels = firebase_service.get_channels()
    print(f"Encontrados {len(channels)} canais para processar")
    print(channels)
    
    for channel in channels:
        print(f"\nProcessando canal: {channel}")
        try:
            # Check if channel exists and has subscriber count
            existing_channel = firebase_service.get_channel(channel)
            
            # Check if the channel was updated within the last day
            if existing_channel and 'updated_at' in existing_channel:
                last_updated = existing_channel['updated_at'].timestamp()
                if time.time() - last_updated < 86400:
                    print(f"Canal {channel} já foi atualizado nas últimas 24 horas.")
                    continue
            
            # Get and update channel info
            channel_info = youtube_service.get_channel_info(channel)
            if channel_info:
                print(f"Informações do canal obtidas: {channel_info['title']}")
                
            # Get recent videos and channel summary
            print("Buscando vídeos recentes...")
            videos, updated_channel_info = youtube_service.get_recent_videos(channel)
            print(f"Encontrados {len(videos)} vídeos nos últimos 7 dias")
            
            # Save videos
            for video in videos:
                existing_video = firebase_service.get_video(video['id'])
                if not existing_video:
                    print(f"Salvando novo vídeo: {video['title']}")
                    firebase_service.save_video_data(video)
            
            # Update channel with new info including weekly summary
            if updated_channel_info:
                print("Salvando novas informações do canal com resumo semanal...")
                firebase_service.save_channel_data(updated_channel_info)
            
            # Respect YouTube API quotas
            print("Aguardando 1 segundo antes do próximo canal...")
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Erro ao processar canal {channel}: {str(e)}")
            continue

    print("\nProcessamento finalizado!")

if __name__ == "__main__":
    main()