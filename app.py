"""
PROFOCO - Plataforma de Reforço Escolar (Versão Acadêmica)
Aplicação principal Streamlit
"""
import streamlit as st
import pandas as pd
from database import Database
from ollama_client import OllamaClient
import json
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="PROFOCO - Plataforma de Reforço Escolar",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialização de sessão
if 'db' not in st.session_state:
    st.session_state.db = Database()
if 'ollama' not in st.session_state:
    st.session_state.ollama = OllamaClient()

# Título principal
st.title("📚 PROFOCO - Plataforma de Reforço Escolar")
st.markdown("**Versão Acadêmica** - Avaliações Diagnósticas e Reforço Personalizado com IA Local")

# Menu lateral
st.sidebar.title("Menu")
pagina = st.sidebar.radio(
    "Navegação",
    ["🏠 Início", "📝 Criar Questionário", "✍️ Responder Questionário", "📊 Dashboard", "🎯 Reforço Personalizado"]
)

# ==================== PÁGINA INICIAL ====================
if pagina == "🏠 Início":
    st.header("Bem-vindo ao PROFOCO!")
    st.markdown("""
    ### Sobre a Plataforma
    
    O PROFOCO é uma plataforma educacional que utiliza Inteligência Artificial local para:
    
    - ✅ **Gerar questionários** personalizados sobre qualquer tópico
    - ✅ **Avaliar desempenho** dos alunos automaticamente
    - ✅ **Identificar dificuldades** específicas de cada aluno
    - ✅ **Gerar reforço** personalizado baseado nas dificuldades identificadas
    
    ### Como Usar
    
    1. **Criar Questionário**: Configure a disciplina e tópico, gere o questionário via IA
    2. **Responder Questionário**: Alunos respondem às questões na interface
    3. **Dashboard**: Visualize métricas e desempenho da turma
    4. **Reforço Personalizado**: Gere exercícios focados nas dificuldades identificadas
    
    ### Privacidade
    
    🔒 **100% Local**: Todos os dados e processamento de IA acontecem localmente no seu computador.
    Nenhum dado de aluno é enviado para a internet.
    """)
    
    # Estatísticas rápidas
    st.subheader("📈 Estatísticas Rápidas")
    col1, col2, col3 = st.columns(3)
    
    questionarios = st.session_state.db.listar_questionarios()
    resultados = st.session_state.db.obter_todos_resultados()
    
    with col1:
        st.metric("Questionários Criados", len(questionarios))
    with col2:
        st.metric("Alunos Avaliados", len(resultados))
    with col3:
        if resultados:
            nota_media = sum(r['nota'] for r in resultados) / len(resultados)
            st.metric("Nota Média Geral", f"{nota_media:.1f}%")
        else:
            st.metric("Nota Média Geral", "N/A")

# ==================== CRIAR QUESTIONÁRIO ====================
elif pagina == "📝 Criar Questionário":
    st.header("Criar Novo Questionário")
    
    with st.form("form_criar_questionario"):
        col1, col2 = st.columns(2)
        
        with col1:
            disciplina = st.text_input("Disciplina", placeholder="Ex: Inglês, Matemática, História...")
        
        with col2:
            topico = st.text_input("Tópico", placeholder="Ex: Verbo To Be, Equações do 2º grau...")
        
        num_questoes = st.slider("Número de Questões", min_value=3, max_value=10, value=5)
        
        submitted = st.form_submit_button("🎲 Gerar Questionário com IA", type="primary")
        
        if submitted:
            if not disciplina or not topico:
                st.error("⚠️ Por favor, preencha a disciplina e o tópico.")
            else:
                with st.spinner("🤖 Gerando questionário com IA... Isso pode levar alguns segundos."):
                    try:
                        questoes = st.session_state.ollama.gerar_questoes(
                            disciplina=disciplina,
                            topico=topico,
                            num_questoes=num_questoes
                        )
                        
                        # Salva no banco de dados
                        questionario_id = st.session_state.db.criar_questionario(
                            disciplina=disciplina,
                            topico=topico,
                            questoes=questoes
                        )
                        
                        st.success(f"✅ Questionário criado com sucesso! ID: {questionario_id}")
                        st.session_state['questionario_criado'] = {
                            'id': questionario_id,
                            'disciplina': disciplina,
                            'topico': topico,
                            'questoes': questoes
                        }
                    except ConnectionError as e:
                        st.error(f"❌ {str(e)}")
                    except Exception as e:
                        st.error(f"❌ Erro ao gerar questionário: {str(e)}")
    
    # Mostra o questionário criado se existir
    if 'questionario_criado' in st.session_state:
        st.subheader("📋 Questionário Gerado")
        q_data = st.session_state['questionario_criado']
        
        st.info(f"**Disciplina:** {q_data['disciplina']} | **Tópico:** {q_data['topico']}")
        
        for i, questao in enumerate(q_data['questoes'], 1):
            with st.expander(f"Questão {i}", expanded=False):
                st.markdown(f"**{questao['pergunta']}**")
                for opcao in questao['opcoes']:
                    st.markdown(f"- {opcao}")
                st.markdown(f"*Resposta correta: {questao['correta']}*")

# ==================== RESPONDER QUESTIONÁRIO ====================
elif pagina == "✍️ Responder Questionário":
    st.header("Responder Questionário")
    
    # Seleciona questionário
    questionarios = st.session_state.db.listar_questionarios()
    
    if not questionarios:
        st.warning("⚠️ Nenhum questionário disponível. Crie um questionário primeiro!")
    else:
        # Seleciona questionário
        questionario_opcoes = {
            f"{q['disciplina']} - {q['topico']} (ID: {q['id']})": q['id']
            for q in questionarios
        }
        
        questionario_selecionado = st.selectbox(
            "Selecione o Questionário",
            options=list(questionario_opcoes.keys())
        )
        
        if questionario_selecionado:
            questionario_id = questionario_opcoes[questionario_selecionado]
            questionario = st.session_state.db.obter_questionario(questionario_id)
            
            if questionario:
                st.info(f"**Disciplina:** {questionario['disciplina']} | **Tópico:** {questionario['topico']}")
                
                # Nome do aluno
                nome_aluno = st.text_input("Nome do Aluno", placeholder="Digite seu nome")
                
                if nome_aluno:
                    st.divider()
                    
                    # Formulário de respostas
                    respostas = []
                    questoes = questionario['questoes']
                    
                    for i, questao in enumerate(questoes):
                        st.markdown(f"### Questão {i + 1}")
                        st.markdown(f"**{questao['pergunta']}**")
                        
                        opcao_selecionada = st.radio(
                            "Selecione sua resposta:",
                            options=['A', 'B', 'C', 'D'],
                            key=f"q_{i}",
                            horizontal=True
                        )
                        
                        # Mostra as opções
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**A)** {questao['opcoes'][0]}")
                            st.markdown(f"**B)** {questao['opcoes'][1]}")
                        with col2:
                            st.markdown(f"**C)** {questao['opcoes'][2]}")
                            st.markdown(f"**D)** {questao['opcoes'][3]}")
                        
                        respostas.append(opcao_selecionada)
                        st.divider()
                    
                    # Botão de envio
                    if st.button("📤 Enviar Respostas", type="primary"):
                        with st.spinner("🤖 Analisando respostas com IA..."):
                            try:
                                analise = st.session_state.ollama.analisar_respostas(
                                    questoes=questoes,
                                    respostas_aluno=respostas,
                                    nome_aluno=nome_aluno,
                                    disciplina=questionario['disciplina'],
                                    topico=questionario['topico']
                                )
                                
                                # Salva resultado
                                st.session_state.db.salvar_resultado(
                                    id_questionario=questionario_id,
                                    nome_aluno=nome_aluno,
                                    respostas=respostas,
                                    nota=analise['nota'],
                                    analise=analise
                                )
                                
                                st.success("✅ Respostas salvas com sucesso!")
                                
                                # Mostra resultado
                                st.subheader("📊 Resultado")
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric("Nota", f"{analise['nota']:.1f}%")
                                with col2:
                                    st.metric("Acertos", f"{analise['acertos']}/{len(questoes)}")
                                with col3:
                                    st.metric("Nível de Domínio", analise['nivel_dominio'])
                                
                                st.markdown(f"**Pontos Fortes:** {analise['pontos_fortes']}")
                                st.markdown(f"**Recomendações:** {analise['recomendacoes']}")
                                
                                if analise['questoes_erradas']:
                                    st.markdown("### ❌ Questões Erradas")
                                    for q_errada in analise['questoes_erradas']:
                                        with st.expander(f"Questão {q_errada['indice']}"):
                                            st.markdown(f"**{q_errada['pergunta']}**")
                                            st.error(f"Sua resposta: {q_errada['resposta_errada']}")
                                            st.success(f"Resposta correta: {q_errada['resposta_correta']}")
                                
                            except Exception as e:
                                st.error(f"❌ Erro ao analisar respostas: {str(e)}")

# ==================== DASHBOARD ====================
elif pagina == "📊 Dashboard":
    st.header("📊 Dashboard de Desempenho")
    
    resultados = st.session_state.db.obter_todos_resultados()
    questionarios = st.session_state.db.listar_questionarios()
    
    if not resultados:
        st.warning("⚠️ Nenhum resultado disponível ainda.")
    else:
        # Métricas gerais
        st.subheader("📈 Métricas Gerais")
        col1, col2, col3, col4 = st.columns(4)
        
        nota_media = sum(r['nota'] for r in resultados) / len(resultados)
        alunos_unicos = len(set(r['nome_aluno'] for r in resultados))
        taxa_aprovacao = sum(1 for r in resultados if r['nota'] >= 70) / len(resultados) * 100
        
        with col1:
            st.metric("Nota Média", f"{nota_media:.1f}%")
        with col2:
            st.metric("Total de Avaliações", len(resultados))
        with col3:
            st.metric("Alunos Únicos", alunos_unicos)
        with col4:
            st.metric("Taxa de Aprovação", f"{taxa_aprovacao:.1f}%")
        
        st.divider()
        
        # Gráfico de notas
        st.subheader("📊 Distribuição de Notas")
        notas = [r['nota'] for r in resultados]
        df_notas = pd.DataFrame({'Nota': notas})
        st.bar_chart(df_notas)
        
        # Tabela de resultados
        st.subheader("📋 Resultados Detalhados")
        
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            disciplinas = ['Todas'] + sorted(set(r['disciplina'] for r in resultados))
            disciplina_filtro = st.selectbox("Filtrar por Disciplina", disciplinas)
        with col2:
            questionarios_opcoes = ['Todos'] + [f"{q['disciplina']} - {q['topico']}" for q in questionarios]
            questionario_filtro = st.selectbox("Filtrar por Questionário", questionarios_opcoes)
        
        # Aplica filtros
        resultados_filtrados = resultados
        if disciplina_filtro != 'Todas':
            resultados_filtrados = [r for r in resultados_filtrados if r['disciplina'] == disciplina_filtro]
        
        # Prepara dados para tabela
        dados_tabela = []
        for r in resultados_filtrados:
            dados_tabela.append({
                'Aluno': r['nome_aluno'],
                'Disciplina': r['disciplina'],
                'Tópico': r['topico'],
                'Nota': f"{r['nota']:.1f}%",
                'Nível': r['analise']['nivel_dominio'],
                'Data': r['data_resposta']
            })
        
        if dados_tabela:
            df = pd.DataFrame(dados_tabela)
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Análise de dificuldades
        st.subheader("🎯 Análise de Dificuldades")
        
        # Coleta tópicos de dificuldade
        topicos_dificuldade = {}
        for r in resultados:
            if r['analise'].get('topicos_dificuldade'):
                for topico in r['analise']['topicos_dificuldade']:
                    if topico not in topicos_dificuldade:
                        topicos_dificuldade[topico] = 0
                    topicos_dificuldade[topico] += 1
        
        if topicos_dificuldade:
            df_dificuldades = pd.DataFrame({
                'Tópico': list(topicos_dificuldade.keys()),
                'Frequência': list(topicos_dificuldade.values())
            }).sort_values('Frequência', ascending=False)
            
            st.bar_chart(df_dificuldades.set_index('Tópico'))
        else:
            st.info("Nenhuma dificuldade identificada ainda.")

# ==================== REFORÇO PERSONALIZADO ====================
elif pagina == "🎯 Reforço Personalizado":
    st.header("🎯 Gerar Reforço Personalizado")
    
    resultados = st.session_state.db.obter_todos_resultados()
    
    if not resultados:
        st.warning("⚠️ Nenhum resultado disponível. É necessário que alunos respondam questionários primeiro.")
    else:
        # Seleciona aluno
        alunos_unicos = sorted(set(r['nome_aluno'] for r in resultados))
        aluno_selecionado = st.selectbox("Selecione o Aluno", alunos_unicos)
        
        if aluno_selecionado:
            # Busca resultados do aluno
            resultados_aluno = [r for r in resultados if r['nome_aluno'] == aluno_selecionado]
            
            st.info(f"**Aluno:** {aluno_selecionado} | **Total de Avaliações:** {len(resultados_aluno)}")
            
            # Mostra histórico do aluno
            st.subheader("📋 Histórico do Aluno")
            dados_historico = []
            for r in resultados_aluno:
                dados_historico.append({
                    'Disciplina': r['disciplina'],
                    'Tópico': r['topico'],
                    'Nota': f"{r['nota']:.1f}%",
                    'Nível': r['analise']['nivel_dominio'],
                    'Data': r['data_resposta']
                })
            
            if dados_historico:
                df_historico = pd.DataFrame(dados_historico)
                st.dataframe(df_historico, use_container_width=True, hide_index=True)
            
            # Identifica dificuldades
            todas_dificuldades = []
            disciplinas_dificuldade = set()
            
            for r in resultados_aluno:
                if r['nota'] < 70:  # Nota abaixo de 70%
                    topicos = r['analise'].get('topicos_dificuldade', [])
                    todas_dificuldades.extend(topicos)
                    disciplinas_dificuldade.add(r['disciplina'])
            
            if not todas_dificuldades:
                st.success("✅ Este aluno não possui dificuldades identificadas (notas acima de 70%).")
            else:
                st.subheader("⚠️ Dificuldades Identificadas")
                topicos_unicos = list(set(todas_dificuldades))
                
                for topico in topicos_unicos:
                    st.markdown(f"- {topico}")
                
                # Seleciona disciplina para reforço
                disciplina_reforco = st.selectbox(
                    "Disciplina para Reforço",
                    options=sorted(disciplinas_dificuldade)
                )
                
                num_questoes_reforco = st.slider(
                    "Número de Questões de Reforço",
                    min_value=3,
                    max_value=10,
                    value=5
                )
                
                if st.button("🎯 Gerar Reforço Personalizado", type="primary"):
                    with st.spinner("🤖 Gerando questões de reforço com IA..."):
                        try:
                            questoes_reforco = st.session_state.ollama.gerar_reforco(
                                topicos_dificuldade=topicos_unicos,
                                disciplina=disciplina_reforco,
                                num_questoes=num_questoes_reforco
                            )
                            
                            st.success(f"✅ {len(questoes_reforco)} questões de reforço geradas!")
                            
                            st.subheader("📝 Questões de Reforço")
                            st.info(f"**Focadas em:** {', '.join(topicos_unicos)}")
                            
                            for i, questao in enumerate(questoes_reforco, 1):
                                with st.expander(f"Questão de Reforço {i}", expanded=True):
                                    st.markdown(f"**{questao['pergunta']}**")
                                    for opcao in questao['opcoes']:
                                        st.markdown(f"- {opcao}")
                                    st.markdown(f"*Resposta correta: {questao['correta']}*")
                            
                            # Opção para salvar como novo questionário
                            if st.button("💾 Salvar como Novo Questionário"):
                                questionario_id = st.session_state.db.criar_questionario(
                                    disciplina=disciplina_reforco,
                                    topico=f"Reforço: {', '.join(topicos_unicos)}",
                                    questoes=questoes_reforco
                                )
                                st.success(f"✅ Questionário de reforço salvo! ID: {questionario_id}")
                        
                        except Exception as e:
                            st.error(f"❌ Erro ao gerar reforço: {str(e)}")

# Rodapé
st.sidebar.markdown("---")
st.sidebar.markdown("**PROFOCO v1.0**")
st.sidebar.markdown("Plataforma de Reforço Escolar")
st.sidebar.markdown("🔒 100% Local e Privado")



