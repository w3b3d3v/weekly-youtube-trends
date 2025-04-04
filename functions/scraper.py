"""
Program Rules and Requirements
----------------------------

1. Channel Processing:
   - Channels must have a valid YouTube channel ID to be processed

2. Video Requirements:
   - Videos must be from the last 7 days
   - Only videos with transcripts are considered for summaries
   - At least one video with transcript is required to generate a channel summary

3. Summary Generation:
   - Individual video summaries are generated for videos with transcripts
   - Weekly channel summaries are created if there's at least one video with transcript
   - Master summary combines all channel summaries from the last 7 days

4. Update Frequency:
   - Channels are only updated if not processed in the last 24 hours
   - Master summary is only generated if none exists for the last 7 days
"""

from firebase_service import FirebaseService
from youtube_service import YouTubeService
from cli import handle_cli_commands
import time
from claude_service import ClaudeService
from datetime import datetime, timedelta, timezone

# Initialize global service instances
firebase_service = FirebaseService()
youtube_service = YouTubeService(firebase_service)
claude_service = ClaudeService(firebase_service)

def process_pending_channels():
    """Process channels with PENDING status to get their channel IDs"""
    print("\nVerificando canais pendentes...")
    pending_channels = firebase_service.get_pending_channels()
    print("pending_channels", pending_channels)
    
    for channel in pending_channels:
        print(f"\nProcessando canal pendente: {channel['title']}")
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

def process_missing_transcripts():
    """
    Process all videos that don't have transcripts yet.
    Fetches transcripts using YouTube API and saves them to Firestore.
    """
    print("\n=== Processando vídeos sem transcrição ===")
    
    # Get all videos without transcripts
    videos = firebase_service.get_videos_without_transcript()
    
    if not videos:
        print("Nenhum vídeo encontrado sem transcrição.")
        return
        
    print(f"Encontrados {len(videos)} vídeos para processar")
    
    for video in videos:
        try:
            print(f"\nBuscando transcrição para: {video['id']}")
            
            # Get transcript from YouTube
            transcript_data = youtube_service.get_video_transcript(video['id'])
            
            # Keep all existing video data
            updated_video = video.copy()
            
            # Only update transcript related fields
            updated_video.update({
                'transcript': transcript_data['transcript'],
                'has_transcript': transcript_data['has_transcript'],
                'updated_at': datetime.now(timezone.utc)
            })
            
            # Save updated video data
            firebase_service.save_video_data(updated_video)
            
            if transcript_data['has_transcript']:
                print(f"✅ Transcrição salva com sucesso para: {video['id']}")
            else:
                print(f"⚠️ Nenhuma transcrição disponível para: {video['id']}")
            
            # Wait a bit to avoid rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Erro ao processar transcrição do vídeo {video['id']}: {str(e)}")
            continue
    
    print("\nProcessamento de transcrições finalizado!")

def check_master_summary_exists(firebase_service):
    """Check if a master summary exists for the last 7 days"""
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7))
    
    # Get the latest master summary
    latest_master = firebase_service.get_latest_master_summary()
    
    if latest_master and 'created_at' in latest_master:
        last_summary_date = latest_master['created_at'].timestamp()
        if time.time() - last_summary_date < 604800:  # 7 days in seconds
            print("Master summary already exists for the last 7 days")
            return True
            
    return False

def generate_master_from_existing_data(firebase_service, claude_service):
    """Generate master summary from existing channel summaries in the last 7 days"""
    print("\nGerando resumo consolidado a partir dos dados existentes...")
    
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7))
    
    # Get all channel summaries from the last 7 days
    weekly_summaries = firebase_service.get_recent_channel_summaries(seven_days_ago)
    
    if weekly_summaries:
        master_summary = claude_service.create_master_weekly_summary(weekly_summaries)
        
        if master_summary['has_master_summary']:
            consolidated_insight = {
                'content': master_summary['master_summary'],
                'type': 'consolidated_weekly',
                'title': 'Resumo Semanal Consolidado',
                'origin_id': 'consolidated_weekly',
                'created_at': datetime.now(timezone.utc)
            }
            firebase_service.save_insight(consolidated_insight)
            print("Resumo consolidado gerado e salvo com sucesso!")
            return True
            
    print("❌ Não foi possível gerar o resumo consolidado dos dados existentes")
    return False

def process_single_channel(channel):
    """Process a single channel and return its weekly summary if available"""
    print(f"\nProcessando canal: {channel['channel_id']}")
    
    try:
        # Skip if updated in last 24 hours
        if 'updated_at' in channel:
            last_updated = channel['updated_at'].timestamp()
            if time.time() - last_updated < 86400:
                print(f"Canal {channel['channel_id']} já foi atualizado nas últimas 24 horas.")
                return None
        
        # Get channel info and recent videos
        print("Buscando informações e vídeos recentes...")
        channel_info = youtube_service.get_channel_info(channel['channel_id'])
        videos = youtube_service.get_recent_videos(channel['channel_id'])
        
        if not channel_info:
            print(f"❌ Não foi possível obter informações do canal {channel['channel_id']}")
            return None
            
        # Save channel info
        updated_channel = {
            **channel_info,
            'doc_id': channel['doc_id']
        }
        
        print(f"Atualizando informações do canal: {channel_info['title']}")
        firebase_service.save_channel_data(updated_channel)

        # Process and save videos and their summaries separately
        print(f"Encontrados {len(videos)} vídeos nos últimos 7 dias")
        
        # First, save all videos and try to get their transcripts
        for video in videos:
            video_exists = firebase_service.get_video(video['id'])
            if not video_exists:
                print(f"Salvando novo vídeo: {video['title']}")
                firebase_service.save_video_data(video)
        
        # Check if at least one video has transcript
        has_any_transcript = False
        videos_with_transcripts = []
        videos_without_transcripts = []
        
        for video in videos:
            video_data = firebase_service.get_video(video['id'])
            if video_data and video_data.get('has_transcript', False):
                has_any_transcript = True
                videos_with_transcripts.append(video_data)
            else:
                print(f"⚠️ Vídeo sem transcrição: {video['title']}")
                videos_without_transcripts.append(video)
        
        if not has_any_transcript:
            print(f"❌ Pulando resumo semanal para {channel_info['title']} - nenhum vídeo tem transcrição")
            return None
            
        print(f"✅ {len(videos_with_transcripts)} vídeos com transcrição encontrados")
        if videos_without_transcripts:
            print(f"⚠️ {len(videos_without_transcripts)} vídeos sem transcrição serão ignorados no resumo")
            
        # Generate and save summaries for videos with transcripts
        videos_with_summaries = []
        for video in videos_with_transcripts:
            summary_data = youtube_service.generate_video_summary(video)
            if summary_data['has_summary']:
                video.update(summary_data)
                videos_with_summaries.append(video)
                
                insight_data = {
                    'content': summary_data['summary'],
                    'origin_id': video['id'],
                    'type': 'video',
                    'title': f"{video['title']}"
                }
                firebase_service.save_insight(insight_data)
        
        # Generate weekly channel summary if we have videos with summaries
        if videos_with_summaries:
            weekly_summary = youtube_service.generate_weekly_channel_summary(
                channel_info['title'],
                videos_with_summaries
            )
            
            if weekly_summary['has_weekly_summary']:
                insight_data = {
                    'content': weekly_summary['weekly_summary'],
                    'origin_id': channel['channel_id'],
                    'type': 'channel',
                    'title': f"{channel_info['title']}",
                    'created_at': datetime.now(timezone.utc)
                }
                firebase_service.save_insight(insight_data)
                
                return {
                    'channel_title': channel_info['title'],
                    'summary': weekly_summary['weekly_summary']
                }
            
        return None
        
    except Exception as e:
        print(f"❌ Erro ao processar canal {channel['channel_id']}: {str(e)}")
        return None

def run_full_process():
    """Run the complete channel processing flow"""
    if handle_cli_commands():
        return
        
    print("Iniciando o processo de atualização...")
    
    # Process any pending channels first -> get channel ID from channel URL
    process_pending_channels()
    
    # Process active channels to update their summaries
    print("\nBuscando canais ativos do Firebase...")
    channels = firebase_service.get_active_channels()
    print(f"Encontrados {len(channels)} canais ativos para processar")
    
    # Store each individual channel weekly summary
    all_weekly_summaries = []
    
    for channel in channels:
        weekly_summary = process_single_channel(channel)
        if weekly_summary:
            all_weekly_summaries.append(weekly_summary)
            
        print("Aguardando 1 segundo antes do próximo canal...")
        time.sleep(1)

    # Check if we already have a recent master summary
    if check_master_summary_exists(firebase_service):
        return
        
    # Try to generate master summary from existing data (including newly updated summaries)
    if generate_master_from_existing_data(firebase_service, claude_service):
        return
    
    # If we have new summaries from channel processing, try to generate master summary
    if all_weekly_summaries:
        print("\nGerando resumo consolidado de todos os canais...")
        master_summary = claude_service.create_master_weekly_summary(all_weekly_summaries)
        
        if master_summary['has_master_summary']:
            consolidated_insight = {
                'content': master_summary['master_summary'],
                'type': 'consolidated_weekly',
                'title': 'Resumo Semanal Consolidado',
                'origin_id': 'consolidated_weekly',
                'created_at': datetime.now(timezone.utc)
            }
            firebase_service.save_insight(consolidated_insight)
            print("Resumo consolidado gerado e salvo com sucesso!")
        else:
            print("❌ Não foi possível gerar o resumo consolidado")
    
    print("\nProcessamento finalizado!")

def main():
    run_full_process()

if __name__ == "__main__":
    main()