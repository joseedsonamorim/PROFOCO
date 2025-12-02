"""
Módulo de integração com Ollama para geração de questões e análise de respostas
"""
import requests
import json
from typing import List, Dict, Optional


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        """
        Inicializa o cliente Ollama
        
        Args:
            base_url: URL base da API do Ollama (padrão: http://localhost:11434)
            model: Nome do modelo a ser usado (padrão: llama3)
        """
        self.base_url = base_url
        self.model = model
        self.api_url = f"{base_url}/api/generate"
    
    def _make_request(self, prompt: str, system: Optional[str] = None) -> str:
        """
        Faz uma requisição à API do Ollama
        
        Args:
            prompt: Prompt para enviar ao modelo
            system: Prompt do sistema (opcional)
        
        Returns:
            Resposta do modelo como string
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json"  # Força resposta em JSON
        }
        
        if system:
            payload["system"] = system
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=120)
            response.raise_for_status()
            return response.json().get("response", "")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Erro: Não foi possível conectar ao Ollama em {self.base_url}. "
                "Certifique-se de que o Ollama está rodando."
            )
        except requests.exceptions.Timeout:
            raise TimeoutError("Erro: Timeout ao comunicar com o Ollama.")
        except Exception as e:
            raise Exception(f"Erro ao comunicar com Ollama: {str(e)}")
    
    def _extract_json(self, text: str) -> Dict:
        """
        Extrai JSON da resposta do modelo, mesmo se houver texto adicional
        
        Args:
            text: Texto da resposta do modelo
        
        Returns:
            Dicionário Python com os dados JSON
        """
        # Tenta encontrar JSON no texto
        text = text.strip()
        
        # Remove markdown code blocks se existirem
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        # Tenta encontrar o primeiro { e último }
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = text[start_idx:end_idx + 1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Se não encontrou JSON válido, tenta parsear o texto inteiro
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            raise ValueError(f"Não foi possível extrair JSON válido da resposta: {text[:200]}")
    
    def gerar_questoes(self, disciplina: str, topico: str, num_questoes: int = 5) -> List[Dict]:
        """
        Gera questões de múltipla escolha sobre um tópico
        
        Args:
            disciplina: Nome da disciplina (ex: "Inglês")
            topico: Tópico específico (ex: "Verbo To Be")
            num_questoes: Número de questões a gerar (padrão: 5)
        
        Returns:
            Lista de dicionários com as questões no formato:
            [{
                'pergunta': '...',
                'opcoes': ['A) ...', 'B) ...', 'C) ...', 'D) ...'],
                'correta': 'A'
            }]
        """
        system_prompt = (
            "Você é um professor especialista. Sua tarefa é criar questões de múltipla escolha "
            "educacionais e didáticas. SEMPRE responda APENAS com um JSON válido, sem texto adicional."
        )
        
        user_prompt = (
            f"Crie {num_questoes} questões de múltipla escolha sobre '{topico}' na disciplina de '{disciplina}'. "
            f"Cada questão deve ter 4 opções (A, B, C, D). "
            f"Formate a resposta EXCLUSIVAMENTE como um JSON válido com a seguinte estrutura: "
            f"[{{'pergunta': 'texto da pergunta', 'opcoes': ['A) opção A', 'B) opção B', 'C) opção C', 'D) opção D'], 'correta': 'A'}}]. "
            f"Não escreva introduções, explicações ou texto adicional. Apenas o JSON."
        )
        
        response = self._make_request(user_prompt, system_prompt)
        data = self._extract_json(response)
        
        # Garante que é uma lista
        if isinstance(data, dict) and 'questoes' in data:
            questoes = data['questoes']
        elif isinstance(data, list):
            questoes = data
        else:
            raise ValueError(f"Formato de resposta inesperado: {type(data)}")
        
        # Valida e formata as questões
        questoes_formatadas = []
        for i, q in enumerate(questoes):
            if not isinstance(q, dict):
                continue
            
            pergunta = q.get('pergunta', '')
            opcoes = q.get('opcoes', [])
            correta = q.get('correta', '').upper()
            
            # Validação básica
            if not pergunta or len(opcoes) != 4 or correta not in ['A', 'B', 'C', 'D']:
                continue
            
            questoes_formatadas.append({
                'pergunta': pergunta,
                'opcoes': opcoes,
                'correta': correta
            })
        
        if len(questoes_formatadas) < num_questoes:
            raise ValueError(
                f"Apenas {len(questoes_formatadas)} questões válidas foram geradas. "
                f"Esperado: {num_questoes}"
            )
        
        return questoes_formatadas[:num_questoes]
    
    def analisar_respostas(self, questoes: List[Dict], respostas_aluno: List[str], 
                          nome_aluno: str, disciplina: str, topico: str) -> Dict:
        """
        Analisa as respostas do aluno e identifica dificuldades
        
        Args:
            questoes: Lista de questões do questionário
            respostas_aluno: Lista com as respostas do aluno (ex: ['A', 'B', 'C'])
            nome_aluno: Nome do aluno
            disciplina: Disciplina do questionário
            topico: Tópico do questionário
        
        Returns:
            Dicionário com análise contendo:
            {
                'nota': float,
                'acertos': int,
                'erros': int,
                'questoes_erradas': [{'indice': int, 'topico': str, 'dificuldade': str}],
                'nivel_dominio': str,
                'recomendacoes': str
            }
        """
        # Calcula nota básica
        acertos = 0
        questoes_erradas = []
        
        for i, (questao, resposta) in enumerate(zip(questoes, respostas_aluno)):
            if resposta.upper() == questao['correta'].upper():
                acertos += 1
            else:
                questoes_erradas.append({
                    'indice': i + 1,
                    'pergunta': questao['pergunta'],
                    'resposta_errada': resposta,
                    'resposta_correta': questao['correta']
                })
        
        nota = (acertos / len(questoes)) * 100
        
        # Usa IA para análise mais detalhada
        system_prompt = (
            "Você é um professor especialista em análise pedagógica. "
            "Analise o desempenho do aluno e forneça insights educacionais. "
            "SEMPRE responda APENAS com um JSON válido, sem texto adicional."
        )
        
        questoes_erradas_str = "\n".join([
            f"Q{i+1}: {q['pergunta']} (Resposta do aluno: {q['resposta_errada']}, Correta: {q['resposta_correta']})"
            for i, q in enumerate(questoes_erradas)
        ])
        
        user_prompt = (
            f"Analise o desempenho do aluno {nome_aluno} em um questionário sobre '{topico}' "
            f"na disciplina de '{disciplina}'. "
            f"Nota: {nota:.1f}% ({acertos}/{len(questoes)} acertos). "
            f"Questões erradas:\n{questoes_erradas_str if questoes_erradas else 'Nenhuma'}\n\n"
            f"Formate a resposta EXCLUSIVAMENTE como um JSON válido com a seguinte estrutura: "
            f"{{'nivel_dominio': 'Iniciante'|'Básico'|'Intermediário'|'Avançado', "
            f"'topicos_dificuldade': ['tópico1', 'tópico2'], "
            f"'recomendacoes': 'texto com recomendações pedagógicas', "
            f"'pontos_fortes': 'texto sobre pontos fortes do aluno'}}. "
            f"Não escreva introduções ou explicações. Apenas o JSON."
        )
        
        try:
            response = self._make_request(user_prompt, system_prompt)
            analise_ia = self._extract_json(response)
        except Exception as e:
            # Se a análise IA falhar, usa análise básica
            analise_ia = {
                'nivel_dominio': 'Básico' if nota < 70 else 'Intermediário' if nota < 90 else 'Avançado',
                'topicos_dificuldade': [topico] if questoes_erradas else [],
                'recomendacoes': f"Focar em revisão do tópico '{topico}'" if questoes_erradas else "Bom desempenho!",
                'pontos_fortes': f"Acertou {acertos} de {len(questoes)} questões."
            }
        
        return {
            'nota': round(nota, 1),
            'acertos': acertos,
            'erros': len(questoes_erradas),
            'questoes_erradas': questoes_erradas,
            'nivel_dominio': analise_ia.get('nivel_dominio', 'Básico'),
            'topicos_dificuldade': analise_ia.get('topicos_dificuldade', [topico] if questoes_erradas else []),
            'recomendacoes': analise_ia.get('recomendacoes', ''),
            'pontos_fortes': analise_ia.get('pontos_fortes', '')
        }
    
    def gerar_reforco(self, topicos_dificuldade: List[str], disciplina: str, num_questoes: int = 3) -> List[Dict]:
        """
        Gera questões de reforço focadas nos tópicos de dificuldade
        
        Args:
            topicos_dificuldade: Lista de tópicos onde o aluno teve dificuldade
            disciplina: Nome da disciplina
            num_questoes: Número de questões a gerar (padrão: 3)
        
        Returns:
            Lista de questões de reforço no mesmo formato de gerar_questoes()
        """
        topicos_str = ", ".join(topicos_dificuldade)
        
        system_prompt = (
            "Você é um professor especialista em reforço escolar. "
            "Crie questões de reforço focadas em ajudar o aluno a superar dificuldades específicas. "
            "SEMPRE responda APENAS com um JSON válido, sem texto adicional."
        )
        
        user_prompt = (
            f"O aluno teve dificuldades nos seguintes tópicos: {topicos_str} na disciplina de '{disciplina}'. "
            f"Gere {num_questoes} questões de reforço focadas EXCLUSIVAMENTE nestes tópicos. "
            f"As questões devem ser mais didáticas e explicativas, ajudando o aluno a compreender melhor. "
            f"Formate a resposta EXCLUSIVAMENTE como um JSON válido com a seguinte estrutura: "
            f"[{{'pergunta': 'texto da pergunta', 'opcoes': ['A) opção A', 'B) opção B', 'C) opção C', 'D) opção D'], 'correta': 'A'}}]. "
            f"Não escreva introduções ou explicações. Apenas o JSON."
        )
        
        response = self._make_request(user_prompt, system_prompt)
        data = self._extract_json(response)
        
        # Garante que é uma lista
        if isinstance(data, dict) and 'questoes' in data:
            questoes = data['questoes']
        elif isinstance(data, list):
            questoes = data
        else:
            raise ValueError(f"Formato de resposta inesperado: {type(data)}")
        
        # Valida e formata as questões
        questoes_formatadas = []
        for q in questoes:
            if not isinstance(q, dict):
                continue
            
            pergunta = q.get('pergunta', '')
            opcoes = q.get('opcoes', [])
            correta = q.get('correta', '').upper()
            
            if not pergunta or len(opcoes) != 4 or correta not in ['A', 'B', 'C', 'D']:
                continue
            
            questoes_formatadas.append({
                'pergunta': pergunta,
                'opcoes': opcoes,
                'correta': correta
            })
        
        return questoes_formatadas[:num_questoes]



