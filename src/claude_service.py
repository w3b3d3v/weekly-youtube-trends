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