from firebase_service import FirebaseService
from youtube_service import YouTubeService
from cli import handle_cli_commands
import time

def process_pending_channels(firebase_service, youtube_service):
    """Process channels with PENDING status to get their channel IDs"""
    print("\nVerificando canais pendentes...")
    pending_channels = firebase_service.get_pending_channels()
    
    for channel in pending_channels:
        print(f"\nProcessando canal pendente: {channel['name']}")
        try:
            channel_id = youtube_service.extract_channel_id_from_url(channel['url'])
            
            if channel_id:
                print(f"ID do canal encontrado: {channel_id}")
                # Update the channel document with the ID and change status to ACTIVE
                firebase_service.update_channel_status(
                    channel['doc_id'],
                    {
                        'channel_id': channel_id,
                        'status': 'ACTIVE'
                    }
                )
            else:
                print(f"❌ Não foi possível encontrar o ID para o canal: {channel['name']}")
                
        except Exception as e:
            print(f"❌ Erro ao processar canal pendente {channel['name']}: {str(e)}")
            continue

def main():
    # Check if there's a CLI command to handle
    if handle_cli_commands():
        return
        
    print("Iniciando o processo de atualização...")
    firebase_service = FirebaseService()
    youtube_service = YouTubeService(firebase_service)
    
    # First process any pending channels
    process_pending_channels(firebase_service, youtube_service)
    
    # Get all active channels from Firebase
    print("\nBuscando canais ativos do Firebase...")
    channels = firebase_service.get_active_channels()
    print(f"Encontrados {len(channels)} canais ativos para processar")
    
    for channel in channels:
        print(f"\nProcessando canal: {channel['channel_id']}")
        try:
            # Skip if updated in last 24 hours
            if 'updated_at' in channel:
                last_updated = channel['updated_at'].timestamp()
                if time.time() - last_updated < 86400:
                    print(f"Canal {channel['channel_id']} já foi atualizado nas últimas 24 horas.")
                    continue
            
            # Get channel info and recent videos
            print("Buscando informações e vídeos recentes...")
            channel_info = youtube_service.get_channel_info(channel['channel_id'])
            videos, weekly_summary = youtube_service.get_recent_videos(channel['channel_id'])
            
            if channel_info:
                # Save channel info without the summary
                updated_channel = {
                    **channel_info,
                    'doc_id': channel['doc_id']  # Keep the Firestore document ID
                }
                
                # Save updated channel info
                print(f"Atualizando informações do canal: {channel_info['title']}")
                firebase_service.save_channel_data(updated_channel)
            
            # Process and save videos and their summaries separately
            print(f"Encontrados {len(videos)} vídeos nos últimos 7 dias")
            for video in videos:
                video_exists = firebase_service.get_video(video['id'])
                if not video_exists:
                    # Extract summary before saving video
                    video_summary = video.pop('summary', None)
                    
                    print(f"Salvando novo vídeo: {video['title']}")
                    firebase_service.save_video_data(video)

                    # Save video summary as an insight if it exists
                    if video_summary:
                        insight_data = {
                            'content': video_summary,
                            'origin_id': video['id'],
                            'type': 'video',
                            'title': f"{video['title']}"
                        }
                        firebase_service.save_insight(insight_data)

            # After processing all videos, save the weekly summary if it exists
            if weekly_summary:
                insight_data = {
                    'content': weekly_summary['weekly_summary'],
                    'origin_id': channel['channel_id'],
                    'type': 'channel',
                    'title': f"{channel_info['title']}"
                }
                firebase_service.save_insight(insight_data)
            
            # Respect YouTube API quotas
            print("Aguardando 1 segundo antes do próximo canal...")
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Erro ao processar canal {channel['channel_id']}: {str(e)}")
            continue

    print("\nProcessamento finalizado!")

if __name__ == "__main__":
    main()