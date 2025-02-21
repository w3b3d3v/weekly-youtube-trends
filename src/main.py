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
    youtube_service = YouTubeService()
    
    # First process any pending channels
    process_pending_channels(firebase_service, youtube_service)
    
    # Get all active channels from Firebase
    print("\nBuscando canais ativos do Firebase...")
    channels = firebase_service.get_active_channels()
    print(f"Encontrados {len(channels)} canais ativos para processar")
    return
    
    for channel in channels:
        print(f"\nProcessando canal: {channel['channel_id']}")
        try:
            # Check if channel exists and has subscriber count
            existing_channel = firebase_service.get_channel(channel['channel_id'])
            
            # Check if the channel was updated within the last day
            if existing_channel and 'updated_at' in existing_channel:
                last_updated = existing_channel['updated_at'].timestamp()
                if time.time() - last_updated < 86400:
                    print(f"Canal {channel['channel_id']} já foi atualizado nas últimas 24 horas.")
                    continue
            
            # Get and update channel info
            channel_info = youtube_service.get_channel_info(channel['channel_id'])
            if channel_info:
                print(f"Informações do canal obtidas: {channel_info['title']}")
                
            # Get recent videos and channel summary
            print("Buscando vídeos recentes...")
            videos, updated_channel_info = youtube_service.get_recent_videos(channel['channel_id'])
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
            print(f"❌ Erro ao processar canal {channel['channel_id']}: {str(e)}")
            continue

    print("\nProcessamento finalizado!")

if __name__ == "__main__":
    main()