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
            response = requests.post(self.api_url, json=payload, timeout=300)
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
    
    def _extract_json(self, text: str):
        """
        Extrai JSON da resposta do modelo, mesmo se houver texto adicional
        
        Args:
            text: Texto da resposta do modelo
        
        Returns:
            Dicionário ou Lista Python com os dados JSON
        """
        # Tenta encontrar JSON no texto
        text = text.strip()
        
        # Remove markdown code blocks se existirem
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        # Tenta encontrar JSON array primeiro (lista começa com [)
        if text.startswith('['):
            end_idx = text.rfind(']')
            if end_idx != -1:
                json_str = text[:end_idx + 1]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
        
        # Tenta encontrar JSON object (começa com {)
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = text[start_idx:end_idx + 1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Tenta encontrar JSON array em qualquer lugar do texto
        start_idx = text.find('[')
        end_idx = text.rfind(']')
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
            raise ValueError(f"Não foi possível extrair JSON válido da resposta: {text[:500]}")
    
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
            "educacionais e didáticas. SEMPRE responda APENAS com um JSON válido, sem texto adicional. "
            "CRÍTICO: Você DEVE retornar uma LISTA/ARRAY JSON, nunca um objeto único."
        )
        
        # Cria exemplo completo para o modelo entender melhor
        exemplo_questoes = ", ".join([
            f"{{'pergunta': 'Questão {i+1} sobre {topico}', 'opcoes': ['A) Opção A da questão {i+1}', 'B) Opção B da questão {i+1}', 'C) Opção C da questão {i+1}', 'D) Opção D da questão {i+1}'], 'correta': '{chr(65+i)}'}}"
            for i in range(min(3, num_questoes))
        ])
        
        # Prompt mais direto e enfático
        user_prompt = (
            f"Você DEVE criar EXATAMENTE {num_questoes} questões de múltipla escolha sobre '{topico}' na disciplina '{disciplina}'. "
            f"\n\nCRÍTICO: Retorne UM ARRAY JSON com {num_questoes} questões. NÃO retorne apenas 1 questão. "
            f"\n\nFormato obrigatório (comece com [ e termine com ]):\n"
            f"[\n"
            f"  {{'pergunta': 'Primeira pergunta sobre {topico}', 'opcoes': ['A) Opção A', 'B) Opção B', 'C) Opção C', 'D) Opção D'], 'correta': 'A'}},\n"
            f"  {{'pergunta': 'Segunda pergunta sobre {topico}', 'opcoes': ['A) Opção A', 'B) Opção B', 'C) Opção C', 'D) Opção D'], 'correta': 'B'}},\n"
            f"  {{'pergunta': 'Terceira pergunta sobre {topico}', 'opcoes': ['A) Opção A', 'B) Opção B', 'C) Opção C', 'D) Opção D'], 'correta': 'C'}}"
            + (f",\n  ... mais {num_questoes - 3} questões" if num_questoes > 3 else "") +
            f"\n]\n\n"
            f"IMPORTANTE: O array deve ter {num_questoes} objetos. Cada objeto é uma questão diferente. "
            f"NÃO retorne apenas 1 questão. Retorne {num_questoes} questões no array."
        )
        
        # Tenta gerar questões (com retry e geração incremental se necessário)
        max_tentativas = 3
        questoes_formatadas_final = []
        
        for tentativa in range(max_tentativas):
            try:
                response = self._make_request(user_prompt, system_prompt)
                data = self._extract_json(response)
                
                # Garante que é uma lista - trata diferentes formatos de resposta
                questoes = None
                if isinstance(data, list):
                    questoes = data
                elif isinstance(data, dict):
                    # Tenta diferentes chaves possíveis
                    if 'questoes' in data:
                        questoes = data['questoes']
                    elif 'questions' in data:
                        questoes = data['questions']
                    elif len(data) == 1 and isinstance(list(data.values())[0], list):
                        # Se o dict tem apenas uma chave e o valor é uma lista
                        questoes = list(data.values())[0]
                    elif any(key.startswith('questao') for key in data.keys()):
                        # Formato com chaves questao1, questao2, etc. - ordena numericamente
                        questoes_numeradas = []
                        chaves_ordenadas = sorted(
                            [k for k in data.keys() if k.startswith('questao')],
                            key=lambda x: int(''.join(filter(str.isdigit, x)) or 999)
                        )
                        for key in chaves_ordenadas:
                            questoes_numeradas.append(data[key])
                        questoes = questoes_numeradas
                    elif any(key.startswith('q') and len(key) > 1 and key[1:].isdigit() for key in data.keys()):
                        # Formato com chaves q1, q2, q3, etc.
                        questoes_numeradas = []
                        chaves_ordenadas = sorted(
                            [k for k in data.keys() if k.startswith('q') and len(k) > 1 and k[1:].isdigit()],
                            key=lambda x: int(x[1:]) if x[1:].isdigit() else 999
                        )
                        for key in chaves_ordenadas:
                            questoes_numeradas.append(data[key])
                        questoes = questoes_numeradas
                    elif all(isinstance(v, dict) for v in data.values()):
                        # Se todos os valores são dicionários (questões), converte para lista
                        questoes = list(data.values())
                    else:
                        # Se o dict tem estrutura de questão única, tenta converter
                        if 'pergunta' in data or 'question' in data:
                            questoes = [data]
                        else:
                            if tentativa < max_tentativas - 1:
                                continue  # Tenta novamente
                            raise ValueError(f"Formato de resposta inesperado: dict com chaves {list(data.keys())[:10]}")
                else:
                    if tentativa < max_tentativas - 1:
                        continue  # Tenta novamente
                    raise ValueError(f"Formato de resposta inesperado: {type(data)}")
                
                if not questoes or not isinstance(questoes, list):
                    if tentativa < max_tentativas - 1:
                        continue  # Tenta novamente
                    raise ValueError(f"Não foi possível extrair lista de questões")
                
                # Valida e formata as questões
                questoes_formatadas = []
                for i, q in enumerate(questoes):
                    if not isinstance(q, dict):
                        continue
                    
                    pergunta = q.get('pergunta', '') or q.get('question', '') or q.get('texto', '')
                    opcoes = q.get('opcoes', []) or q.get('options', []) or q.get('alternativas', [])
                    correta = q.get('correta', '').upper() or q.get('correct', '').upper() or q.get('resposta_correta', '').upper()
                    
                    # Validação básica
                    if not pergunta:
                        continue
                    
                    # Normaliza opções - remove prefixos A), B), etc. se existirem
                    opcoes_normalizadas = []
                    for opcao in opcoes:
                        if isinstance(opcao, str):
                            opcao_limpa = opcao.strip()
                            if len(opcao_limpa) > 2 and opcao_limpa[1] in [')', '.', ':']:
                                opcao_limpa = opcao_limpa[2:].strip()
                            opcoes_normalizadas.append(opcao_limpa)
                        else:
                            opcoes_normalizadas.append(str(opcao))
                    
                    # Se não tem 4 opções, completa
                    if len(opcoes_normalizadas) < 4:
                        while len(opcoes_normalizadas) < 4:
                            opcoes_normalizadas.append("Opção não disponível")
                    elif len(opcoes_normalizadas) > 4:
                        opcoes_normalizadas = opcoes_normalizadas[:4]
                    
                    # Normaliza resposta correta
                    if not correta or correta not in ['A', 'B', 'C', 'D']:
                        correta = 'A'
                    
                    questoes_formatadas.append({
                        'pergunta': pergunta,
                        'opcoes': opcoes_normalizadas,
                        'correta': correta
                    })
                
                # Se gerou questões válidas, adiciona à lista final
                if len(questoes_formatadas) > 0:
                    questoes_formatadas_final.extend(questoes_formatadas)
                    
                    # Se já tem questões suficientes, para
                    if len(questoes_formatadas_final) >= num_questoes:
                        break
                    
                    # Se gerou apenas 1 questão e precisa de mais, tenta gerar as restantes
                    if len(questoes_formatadas) == 1 and len(questoes_formatadas_final) < num_questoes:
                        questoes_restantes = num_questoes - len(questoes_formatadas_final)
                        # Gera as questões restantes em uma nova requisição
                        try:
                            prompt_incremental = (
                                f"Você DEVE criar EXATAMENTE {questoes_restantes} questões de múltipla escolha sobre '{topico}' na disciplina '{disciplina}'. "
                                f"Retorne UM ARRAY JSON com {questoes_restantes} questões diferentes das anteriores. "
                                f"Formato: [{{'pergunta': '...', 'opcoes': ['A) ...', 'B) ...', 'C) ...', 'D) ...'], 'correta': 'A'}}, ...]"
                            )
                            response_inc = self._make_request(prompt_incremental, system_prompt)
                            data_inc = self._extract_json(response_inc)
                            
                            # Processa questões incrementais
                            questoes_inc = None
                            if isinstance(data_inc, list):
                                questoes_inc = data_inc
                            elif isinstance(data_inc, dict):
                                if 'questoes' in data_inc or 'questions' in data_inc:
                                    questoes_inc = data_inc.get('questoes') or data_inc.get('questions')
                                elif all(isinstance(v, dict) for v in data_inc.values()):
                                    questoes_inc = list(data_inc.values())
                            
                            if questoes_inc and isinstance(questoes_inc, list):
                                # Formata questões incrementais
                                for q in questoes_inc:
                                    if isinstance(q, dict):
                                        pergunta = q.get('pergunta', '') or q.get('question', '')
                                        opcoes = q.get('opcoes', []) or q.get('options', [])
                                        correta = q.get('correta', 'A').upper()
                                        
                                        if pergunta:
                                            opcoes_norm = []
                                            for op in opcoes[:4]:
                                                if isinstance(op, str):
                                                    op_limpa = op.strip()
                                                    if len(op_limpa) > 2 and op_limpa[1] in [')', '.', ':']:
                                                        op_limpa = op_limpa[2:].strip()
                                                    opcoes_norm.append(op_limpa)
                                                else:
                                                    opcoes_norm.append(str(op))
                                            
                                            while len(opcoes_norm) < 4:
                                                opcoes_norm.append("Opção não disponível")
                                            
                                            questoes_formatadas_final.append({
                                                'pergunta': pergunta,
                                                'opcoes': opcoes_norm[:4],
                                                'correta': correta if correta in ['A', 'B', 'C', 'D'] else 'A'
                                            })
                                            
                                            if len(questoes_formatadas_final) >= num_questoes:
                                                break
                        except:
                            pass  # Se falhar, continua com o que tem
                        
            except Exception as e:
                if tentativa < max_tentativas - 1:
                    continue  # Tenta novamente
                raise  # Re-raise na última tentativa
        
        # Remove duplicatas mantendo ordem
        questoes_unicas = []
        perguntas_vistas = set()
        for q in questoes_formatadas_final:
            pergunta_hash = hash(q.get('pergunta', ''))
            if pergunta_hash not in perguntas_vistas:
                perguntas_vistas.add(pergunta_hash)
                questoes_unicas.append(q)
        
        if len(questoes_unicas) == 0:
            raise ValueError("Nenhuma questão válida foi gerada após múltiplas tentativas. Tente novamente.")
        
        # Retorna as questões formatadas
        return questoes_unicas[:num_questoes]
    
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
        
        # Garante que é uma lista - trata diferentes formatos de resposta
        questoes = None
        if isinstance(data, list):
            questoes = data
        elif isinstance(data, dict):
            # Tenta diferentes chaves possíveis
            if 'questoes' in data:
                questoes = data['questoes']
            elif 'questions' in data:
                questoes = data['questions']
            elif 'questoes_reforco' in data:
                questoes = data['questoes_reforco']
            elif len(data) == 1 and isinstance(list(data.values())[0], list):
                # Se o dict tem apenas uma chave e o valor é uma lista
                questoes = list(data.values())[0]
            elif any(key.startswith('questao') for key in data.keys()):
                # Formato com chaves questao1, questao2, etc.
                questoes = [data[key] for key in sorted(data.keys()) if key.startswith('questao')]
            elif all(isinstance(v, dict) for v in data.values()):
                # Se todos os valores são dicionários (questões), converte para lista
                questoes = list(data.values())
            else:
                # Se o dict tem estrutura de questão única, tenta converter
                if 'pergunta' in data or 'question' in data:
                    questoes = [data]
                else:
                    raise ValueError(f"Formato de resposta inesperado: dict com chaves {list(data.keys())}")
        else:
            raise ValueError(f"Formato de resposta inesperado: {type(data)}")
        
        if not questoes or not isinstance(questoes, list):
            raise ValueError(f"Não foi possível extrair lista de questões do formato: {type(data)}")
        
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



