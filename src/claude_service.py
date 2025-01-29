from anthropic import Anthropic
import os

class ClaudeService:
    def __init__(self):
        print("Inicializando serviço do Claude...")
        self.anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    def summarize_transcript(self, transcript, video_title):
        """Generate a summary of the video transcript using Claude"""
        if not transcript:
            return {
                'summary': '',
                'has_summary': False
            }

        try:
            prompt = f"""Por favor, faça um resumo conciso do seguinte vídeo intitulado "{video_title}". 
            Mantenha o resumo em aproximadamente 3-4 parágrafos.
            
            Transcrição:
            {transcript}"""

            message = self.anthropic.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
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

    def create_weekly_channel_summary(self, channel_title, videos):
        """Create a summary of the channel's content for the past week"""
        try:
            # Filter videos with summaries
            videos_with_summaries = [v for v in videos if v.get('has_summary', False)]
            
            if not videos_with_summaries:
                return {
                    'weekly_summary': '',
                    'has_weekly_summary': False
                }

            # Create a comprehensive prompt with all video information
            videos_info = "\n\n".join([
                f"Vídeo: {v['title']}\nResumo: {v['summary']}"
                for v in videos_with_summaries
            ])

            prompt = f"""Analise os vídeos do canal "{channel_title}" publicados na última semana e crie um resumo geral 
            destacando os principais temas e assuntos abordados. Liste os tópicos mais relevantes e identifique 
            padrões ou séries de conteúdo.

            Dados dos vídeos da semana:
            {videos_info}"""

            message = self.anthropic.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
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