# PROFOCO - Plataforma de Reforço Escolar (Versão Acadêmica)

## Descrição
Aplicação web local para auxiliar professores na criação de avaliações diagnósticas e geração de reforço escolar personalizado usando Inteligência Artificial local (Ollama).

## Características
-  Geração automática de questionários via IA local
-  Análise de desempenho dos alunos
-  Dashboard com métricas e visualizações
-  Geração de reforço personalizado baseado em dificuldades
-  100% local e privado (sem envio de dados para internet)

## Pré-requisitos
1. Python 3.8 ou superior
2. Ollama instalado e configurado
3. Modelo Llama3 ou Mistral baixado no Ollama

## Instalação

### 1. Instalar dependências Python
```bash
pip install -r requirements.txt
```

### 2. Instalar e configurar Ollama
```bash
# Instalar Ollama (macOS)
brew install ollama

# Ou baixar de: https://ollama.ai

# Baixar modelo Llama3
ollama pull llama3

# Ou Mistral
ollama pull mistral
```

## Execução
```bash
streamlit run app.py
```

A aplicação será aberta automaticamente no navegador em `http://localhost:8501`

## Estrutura do Projeto
```
PROFOCO/
├── app.py                 # Aplicação principal Streamlit
├── database.py            # Gerenciamento do banco de dados SQLite
├── ollama_client.py       # Cliente para integração com Ollama
├── requirements.txt       # Dependências Python
├── README.md             # Este arquivo
└── profoco.db            # Banco de dados SQLite (criado automaticamente)
```

## Uso

### Para Professores:

#### 1. Criar Questionário
- Acesse a página "📝 Criar Questionário"
- Informe a disciplina (ex: Inglês, Matemática)
- Informe o tópico específico (ex: Verbo To Be, Equações do 2º grau)
- Selecione o número de questões (3 a 10)
- Clique em "Gerar Questionário com IA"
- O sistema gerará automaticamente questões de múltipla escolha

#### 2. Dashboard de Desempenho
- Acesse a página "📊 Dashboard"
- Visualize métricas gerais (nota média, taxa de aprovação, etc.)
- Analise a distribuição de notas
- Veja resultados detalhados de cada aluno
- Identifique tópicos com maior dificuldade

#### 3. Reforço Personalizado
- Acesse a página "Reforço Personalizado"
- Selecione um aluno
- O sistema identifica automaticamente as dificuldades (notas < 70%)
- Gere questões de reforço focadas nos tópicos problemáticos
- Salve como novo questionário para aplicação

### Para Alunos:

#### 1. Responder Questionário
- Acesse a página "Responder Questionário"
- Selecione o questionário desejado
- Informe seu nome
- Responda todas as questões
- Clique em "Enviar Respostas"

#### 2. Visualizar Resultado
- Após enviar, visualize sua nota e desempenho
- Veja quais questões foram erradas
- Leia as recomendações personalizadas da IA
- Identifique seu nível de domínio

## Tecnologias
- **Frontend/Backend**: Streamlit (Python)
- **IA Local**: Ollama (Llama3/Mistral)
- **Banco de Dados**: SQLite
- **Formato de Dados**: JSON

