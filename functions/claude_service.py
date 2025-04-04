from anthropic import Anthropic
from firebase_service import FirebaseService
from config import ANTHROPIC_API_KEY
import os

class ClaudeService:
    def __init__(self, firebase_service):
        print("Inicializando serviço do Claude...")
        self.anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.firebase_service = firebase_service

    def summarize_transcript(self, transcript, video_title, custom_prompt=None):
        """Generate a summary of the video transcript using Claude"""
        if not transcript:
            return {
                'summary': '',
                'has_summary': False
            }

        try:
            prompt = ""
            if custom_prompt:
                # Use custom prompt if provided
                prompt = f"{custom_prompt}\n\nVídeo: {video_title}\n\nTranscrição:\n{transcript}"
            else:
                # Get prompt from Firebase
                latest_prompt = self.firebase_service.get_latest_prompt()
                
                if not latest_prompt or 'video_summary_prompt' not in latest_prompt:
                    print("❌ Prompt não encontrado no Firestore")
                    return {
                        'summary': '',
                        'has_summary': False
                    }

                # Replace parameters in prompt template
                prompt_template = latest_prompt['video_summary_prompt']
                replacements = {
                    '%VIDEO_TITLE': video_title,
                }
                
                for key, value in replacements.items():
                    if value:  # Only replace if value is not empty
                        prompt_template = prompt_template.replace(key, value)

                prompt = f"{prompt_template}\n{transcript}"

            message = self.anthropic.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4096,
                temperature=0.7,
                system="Você é um assistente especializado em criar resumos concisos e informativos de conteúdo em vídeo. Listando os temas discutidos de forma clara",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract just the text content from the message
            summary_text = message.content[0].text if isinstance(message.content, list) else message.content.text

            return {
                'summary': summary_text,
                'has_summary': True
            }
        except Exception as e:
            print(f"❌ Erro ao gerar resumo: {str(e)}")
            return {
                'summary': '',
                'has_summary': False
            }

    def create_weekly_channel_summary(self, channel_name, videos):
        """Create a summary of the channel's content for the past week"""
        try:
            # Filter videos with summaries
            videos_with_summaries = [v for v in videos if v.get('has_summary', False)]
            
            if not videos_with_summaries:
                return {
                    'weekly_summary': '',
                    'has_weekly_summary': False
                }

            # Get prompt from Firebase
            latest_prompt = self.firebase_service.get_latest_prompt()
            if not latest_prompt or 'channel_weekly_summary_prompt' not in latest_prompt:
                print("❌ Prompt não encontrado no Firestore")
                return {
                    'weekly_summary': '',
                    'has_weekly_summary': False
                }

            # Replace parameters in prompt template
            prompt_template = latest_prompt['channel_weekly_summary_prompt']
            replacements = {
                '%CHANNEL_NAME': channel_name,
            }
            
            for key, value in replacements.items():
                if value:  # Only replace if value is not empty
                    prompt_template = prompt_template.replace(key, value)

            # Create a comprehensive prompt with all video information
            videos_info = "\n\n".join([
                f"Vídeo: {v['title']}\nResumo: {v['summary']}"
                for v in videos_with_summaries
            ])

            prompt = f"{prompt_template}\n{videos_info}"

            message = self.anthropic.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4096,
                temperature=0.7,
                system="Você é um assistente especializado em analisar conteúdo de canais do YouTube e identificar padrões e temas principais.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            summary_text = message.content[0].text if isinstance(message.content, list) else message.content.text

            return {
                'weekly_summary': summary_text,
                'has_weekly_summary': True
            }
        except Exception as e:
            print(f"❌ Erro ao gerar resumo semanal do canal: {str(e)}")
            return {
                'weekly_summary': '',
                'has_weekly_summary': False
            }

    def create_master_weekly_summary(self, channel_summaries):
        """Create a consolidated summary of all channels' weekly content"""
        try:
            if not channel_summaries:
                return {
                    'master_summary': '',
                    'has_master_summary': False
                }

            # Get prompt from Firebase
            latest_prompt = self.firebase_service.get_latest_prompt()
            if not latest_prompt or 'master_weekly_summary_prompt' not in latest_prompt:
                print("❌ Prompt não encontrado no Firestore")
                return {
                    'master_summary': '',
                    'has_master_summary': False
                }

            # Create a comprehensive prompt with all channel summaries
            channels_info = "\n\n".join([
                f"Canal: {summary['channel_title']}\n{summary['summary']}"
                for summary in channel_summaries
            ])

            prompt = f"{latest_prompt['master_weekly_summary_prompt']}\n\n{channels_info}"

            message = self.anthropic.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4096,
                temperature=0.7,
                system="Você é um especialista em análise de conteúdo digital, capaz de identificar tendências e conexões entre diferentes canais e tópicos.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            summary_text = message.content[0].text if isinstance(message.content, list) else message.content.text

            return {
                'master_summary': summary_text,
                'has_master_summary': True
            }
        except Exception as e:
            print(f"❌ Erro ao gerar resumo master semanal: {str(e)}")
            return {
                'master_summary': '',
                'has_master_summary': False
            } 