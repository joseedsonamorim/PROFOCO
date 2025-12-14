"""
PROFOCO - Plataforma de Reforço Escolar (Versão Acadêmica)
Aplicação principal Streamlit com dashboards separados para Aluno e Professor
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
    # Usando modelo menor e mais rápido para evitar timeouts
    # Opções disponíveis: "llama3.2:3b" (recomendado), "llama3", "llama2:7b"
    st.session_state.ollama = OllamaClient(model="llama3.2:3b")
if 'perfil' not in st.session_state:
    st.session_state.perfil = None
if 'aluno_autenticado' not in st.session_state:
    st.session_state.aluno_autenticado = None

# ==================== SELEÇÃO DE PERFIL ====================
if st.session_state.perfil is None:
    st.title("📚 PROFOCO - Plataforma de Reforço Escolar")
    st.markdown("**Versão Acadêmica** - Avaliações Diagnósticas e Reforço Personalizado com IA Local")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👨‍🎓 Área do Aluno")
        st.markdown("""
        - Responder questionários
        - Ver seu desempenho
        - Acessar reforço personalizado
        """)
        if st.button("Entrar como Aluno", type="primary", use_container_width=True):
            st.session_state.perfil = "aluno"
            st.rerun()
    
    with col2:
        st.subheader("👨‍🏫 Área do Professor")
        st.markdown("""
        - Criar questionários
        - Visualizar dashboard
        - Gerenciar avaliações
        """)
        if st.button("Entrar como Professor", type="primary", use_container_width=True):
            st.session_state.perfil = "professor"
            st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**PROFOCO v1.0**")
    st.sidebar.markdown("Plataforma de Reforço Escolar")
    st.sidebar.markdown("🔒 100% Local e Privado")
    
    st.stop()

# ==================== AUTENTICAÇÃO DO ALUNO ====================
if st.session_state.perfil == "aluno" and st.session_state.aluno_autenticado is None:
    st.title("👨‍🎓 Área do Aluno")
    st.markdown("### 🔐 Autenticação")
    
    with st.form("form_autenticacao_aluno"):
        identificador = st.text_input(
            "Nome ou Matrícula",
            placeholder="Digite seu nome ou número de matrícula",
            help="Você pode usar seu nome completo ou número de matrícula"
        )
        
        submitted = st.form_submit_button("Entrar", type="primary")
        
        if submitted:
            if not identificador:
                st.error("⚠️ Por favor, informe seu nome ou matrícula.")
            else:
                # Tenta autenticar
                aluno = st.session_state.db.autenticar_aluno(identificador.strip())
                
                if aluno:
                    st.session_state.aluno_autenticado = aluno
                    st.success(f"✅ Bem-vindo, {aluno['nome']}!")
                    st.rerun()
                else:
                    # Aluno não encontrado - oferece cadastro
                    st.warning("⚠️ Aluno não encontrado. Deseja se cadastrar?")
                    
                    with st.form("form_cadastro_aluno"):
                        nome = st.text_input("Nome Completo", value=identificador if not identificador.isdigit() else "")
                        matricula = st.text_input("Matrícula (opcional)", value=identificador if identificador.isdigit() else "")
                        cadastrar = st.form_submit_button("Cadastrar", type="primary")
                        
                        if cadastrar:
                            if not nome:
                                st.error("⚠️ O nome é obrigatório.")
                            else:
                                try:
                                    aluno_id = st.session_state.db.criar_aluno(nome, matricula if matricula else None)
                                    aluno = st.session_state.db.autenticar_aluno(nome if nome else matricula)
                                    st.session_state.aluno_autenticado = aluno
                                    st.success(f"✅ Cadastro realizado! Bem-vindo, {aluno['nome']}!")
                                    st.rerun()
                                except ValueError as e:
                                    st.error(f"❌ {str(e)}")
    
    st.sidebar.markdown("---")
    if st.sidebar.button("← Voltar"):
        st.session_state.perfil = None
        st.rerun()
    
    st.stop()

# ==================== DASHBOARD DO ALUNO ====================
if st.session_state.perfil == "aluno" and st.session_state.aluno_autenticado:
    aluno = st.session_state.aluno_autenticado
    
    st.title("👨‍🎓 Área do Aluno")
    st.sidebar.title(f"Olá, {aluno['nome']}!")
    if aluno['matricula']:
        st.sidebar.markdown(f"**Matrícula:** {aluno['matricula']}")
    
    # Menu lateral do aluno
    pagina_aluno = st.sidebar.radio(
        "Menu",
        ["🏠 Início", "✍️ Responder Questionário", "🎯 Reforço Personalizado"]
    )
    
    # Botão de logout
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Sair"):
        st.session_state.aluno_autenticado = None
        st.session_state.perfil = None
        st.rerun()
    
    # ========== INÍCIO DO ALUNO ==========
    if pagina_aluno == "🏠 Início":
        st.header(f"Bem-vindo, {aluno['nome']}!")
        
        # Estatísticas do aluno
        resultados_aluno = st.session_state.db.obter_resultados_aluno(
            nome_aluno=aluno['nome'],
            matricula=aluno['matricula']
        )
        
        if resultados_aluno:
            st.subheader("📊 Seu Desempenho")
            col1, col2, col3 = st.columns(3)
            
            nota_media = sum(r['nota'] for r in resultados_aluno) / len(resultados_aluno)
            melhor_nota = max(r['nota'] for r in resultados_aluno)
            total_avaliacoes = len(resultados_aluno)
            
            with col1:
                st.metric("Nota Média", f"{nota_media:.1f}%")
            with col2:
                st.metric("Melhor Nota", f"{melhor_nota:.1f}%")
            with col3:
                st.metric("Total de Avaliações", total_avaliacoes)
            
            st.divider()
            
            st.subheader("📋 Histórico de Avaliações")
            dados_historico = []
            for r in resultados_aluno:
                dados_historico.append({
                    'Disciplina': r['disciplina'],
                    'Tópico': r['topico'],
                    'Nota': f"{r['nota']:.1f}%",
                    'Nível': r['analise']['nivel_dominio'],
                    'Data': r['data_resposta']
                })
            
            df_historico = pd.DataFrame(dados_historico)
            st.dataframe(df_historico, use_container_width=True, hide_index=True)
        else:
            st.info("📝 Você ainda não respondeu nenhum questionário. Acesse 'Responder Questionário' para começar!")
    
    # ========== RESPONDER QUESTIONÁRIO (ALUNO) ==========
    elif pagina_aluno == "✍️ Responder Questionário":
        st.header("Responder Questionário")
        
        questionarios = st.session_state.db.listar_questionarios()
        
        if not questionarios:
            st.warning("⚠️ Nenhum questionário disponível no momento.")
        else:
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
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**A)** {questao['opcoes'][0]}")
                            st.markdown(f"**B)** {questao['opcoes'][1]}")
                        with col2:
                            st.markdown(f"**C)** {questao['opcoes'][2]}")
                            st.markdown(f"**D)** {questao['opcoes'][3]}")
                        
                        respostas.append(opcao_selecionada)
                        st.divider()
                    
                    if st.button("📤 Enviar Respostas", type="primary"):
                        with st.spinner("🤖 Analisando respostas com IA..."):
                            try:
                                analise = st.session_state.ollama.analisar_respostas(
                                    questoes=questoes,
                                    respostas_aluno=respostas,
                                    nome_aluno=aluno['nome'],
                                    disciplina=questionario['disciplina'],
                                    topico=questionario['topico']
                                )
                                
                                # Salva resultado
                                st.session_state.db.salvar_resultado(
                                    id_questionario=questionario_id,
                                    nome_aluno=aluno['nome'],
                                    respostas=respostas,
                                    nota=analise['nota'],
                                    analise=analise,
                                    matricula_aluno=aluno['matricula']
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
    
    # ========== REFORÇO PERSONALIZADO (ALUNO) ==========
    elif pagina_aluno == "🎯 Reforço Personalizado":
        st.header("🎯 Meu Reforço Personalizado")
        
        resultados_aluno = st.session_state.db.obter_resultados_aluno(
            nome_aluno=aluno['nome'],
            matricula=aluno['matricula']
        )
        
        if not resultados_aluno:
            st.info("📝 Você ainda não possui resultados. Responda questionários para gerar reforço personalizado.")
        else:
            # Identifica dificuldades
            todas_dificuldades = []
            disciplinas_dificuldade = set()
            
            for r in resultados_aluno:
                if r['nota'] < 70:  # Nota abaixo de 70%
                    topicos = r['analise'].get('topicos_dificuldade', [])
                    todas_dificuldades.extend(topicos)
                    disciplinas_dificuldade.add(r['disciplina'])
            
            if not todas_dificuldades:
                st.success("✅ Parabéns! Você não possui dificuldades identificadas (todas as notas acima de 70%).")
            else:
                st.subheader("⚠️ Suas Dificuldades Identificadas")
                topicos_unicos = list(set(todas_dificuldades))
                
                for topico in topicos_unicos:
                    st.markdown(f"- {topico}")
                
                st.divider()
                
                if disciplinas_dificuldade:
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
                        with st.spinner("🤖 Gerando questões de reforço com IA... Isso pode levar alguns minutos. Por favor, aguarde..."):
                            try:
                                questoes_reforco = st.session_state.ollama.gerar_reforco(
                                    topicos_dificuldade=topicos_unicos,
                                    disciplina=disciplina_reforco,
                                    num_questoes=num_questoes_reforco
                                )
                                
                                st.success(f"✅ {len(questoes_reforco)} questões de reforço geradas!")
                                
                                # Salva as questões no session_state para uso no formulário
                                st.session_state['questoes_reforco'] = questoes_reforco
                                st.session_state['topicos_reforco'] = topicos_unicos
                                st.rerun()
                            except ConnectionError as e:
                                st.error(f"❌ {str(e)}")
                                st.info("💡 **Dica:** Certifique-se de que o Ollama está rodando. Execute `ollama serve` em um terminal.")
                            except TimeoutError as e:
                                st.error(f"❌ {str(e)}")
                                st.warning("""
                                **💡 Dicas para resolver:**
                                - Tente usar um modelo menor: `ollama pull llama3.2:3b`
                                - Tente gerar menos questões por vez
                                - Verifique se há outros processos usando muitos recursos
                                """)
                            except Exception as e:
                                st.error(f"❌ Erro ao gerar reforço: {str(e)}")
                                st.info("💡 Verifique se o Ollama está rodando e se o modelo está instalado corretamente.")
                
                # Exibe formulário de resposta se houver questões de reforço
                if 'questoes_reforco' in st.session_state and st.session_state['questoes_reforco']:
                    questoes_reforco = st.session_state['questoes_reforco']
                    topicos_reforco = st.session_state.get('topicos_reforco', [])
                    
                    st.subheader("📝 Questões de Reforço")
                    st.info(f"**Focadas em:** {', '.join(topicos_reforco)}")
                    st.markdown("**Responda as questões abaixo e depois clique em 'Verificar Respostas' para ver seu desempenho.**")
                    st.divider()
                    
                    # Formulário de respostas
                    respostas_reforco = []
                    
                    for i, questao in enumerate(questoes_reforco):
                        st.markdown(f"### Questão {i + 1}")
                        st.markdown(f"**{questao['pergunta']}**")
                        
                        opcao_selecionada = st.radio(
                            "Selecione sua resposta:",
                            options=['A', 'B', 'C', 'D'],
                            key=f"reforco_q_{i}",
                            horizontal=True
                        )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**A)** {questao['opcoes'][0]}")
                            st.markdown(f"**B)** {questao['opcoes'][1]}")
                        with col2:
                            st.markdown(f"**C)** {questao['opcoes'][2]}")
                            st.markdown(f"**D)** {questao['opcoes'][3]}")
                        
                        respostas_reforco.append(opcao_selecionada)
                        st.divider()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Verificar Respostas", type="primary", use_container_width=True):
                            # Calcula resultado
                            acertos = 0
                            questoes_erradas = []
                            
                            for i, (questao, resposta) in enumerate(zip(questoes_reforco, respostas_reforco)):
                                if resposta.upper() == questao['correta'].upper():
                                    acertos += 1
                                else:
                                    questoes_erradas.append({
                                        'indice': i + 1,
                                        'pergunta': questao['pergunta'],
                                        'resposta_errada': resposta,
                                        'resposta_correta': questao['correta']
                                    })
                            
                            nota = (acertos / len(questoes_reforco)) * 100
                            
                            # Salva resultado no session_state para exibição
                            st.session_state['resultado_reforco'] = {
                                'nota': nota,
                                'acertos': acertos,
                                'total': len(questoes_reforco),
                                'questoes_erradas': questoes_erradas
                            }
                            st.rerun()
                    
                    with col2:
                        if st.button("🔄 Gerar Novo Reforço", use_container_width=True):
                            if 'questoes_reforco' in st.session_state:
                                del st.session_state['questoes_reforco']
                            if 'resultado_reforco' in st.session_state:
                                del st.session_state['resultado_reforco']
                            st.rerun()
                    
                    # Exibe resultado se houver
                    if 'resultado_reforco' in st.session_state:
                        resultado = st.session_state['resultado_reforco']
                        
                        st.divider()
                        st.subheader("📊 Resultado do Reforço")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Nota", f"{resultado['nota']:.1f}%")
                        with col2:
                            st.metric("Acertos", f"{resultado['acertos']}/{resultado['total']}")
                        with col3:
                            if resultado['nota'] >= 70:
                                st.metric("Status", "✅ Aprovado")
                            else:
                                st.metric("Status", "⚠️ Precisa estudar mais")
                        
                        if resultado['questoes_erradas']:
                            st.markdown("### ❌ Questões Erradas")
                            for q_errada in resultado['questoes_erradas']:
                                with st.expander(f"Questão {q_errada['indice']}"):
                                    st.markdown(f"**{q_errada['pergunta']}**")
                                    st.error(f"Sua resposta: {q_errada['resposta_errada']}")
                                    st.success(f"Resposta correta: {q_errada['resposta_correta']}")
                        else:
                            st.success("🎉 Parabéns! Você acertou todas as questões!")

# ==================== DASHBOARD DO PROFESSOR ====================
elif st.session_state.perfil == "professor":
    st.title("👨‍🏫 Área do Professor")
    
    # Menu lateral do professor
    pagina_professor = st.sidebar.radio(
        "Menu",
        ["🏠 Início", "📝 Criar Questionário", "👥 Gerenciar Alunos", "📊 Dashboard"]
    )
    
    # Botão de logout
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Sair"):
        st.session_state.perfil = None
        st.rerun()
    
    # ========== INÍCIO DO PROFESSOR ==========
    if pagina_professor == "🏠 Início":
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
        2. **Dashboard**: Visualize métricas e desempenho da turma
        3. **Análise**: Identifique tópicos com maior dificuldade
        
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
    
    # ========== CRIAR QUESTIONÁRIO (PROFESSOR) ==========
    elif pagina_professor == "📝 Criar Questionário":
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
                    with st.spinner("🤖 Gerando questionário com IA... Isso pode levar alguns minutos, especialmente com modelos maiores. Por favor, aguarde..."):
                        try:
                            questoes = st.session_state.ollama.gerar_questoes(
                                disciplina=disciplina,
                                topico=topico,
                                num_questoes=num_questoes
                            )
                            
                            # Avisa se foram geradas menos questões que o esperado
                            if len(questoes) < num_questoes:
                                st.warning(f"⚠️ Foram geradas {len(questoes)} questões válidas (esperado: {num_questoes}). O questionário foi criado com as questões disponíveis.")
                            
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
                            st.info("💡 **Dica:** Certifique-se de que o Ollama está rodando. Execute `ollama serve` em um terminal.")
                        except TimeoutError as e:
                            st.error(f"❌ {str(e)}")
                            st.warning("""
                            **💡 Dicas para resolver:**
                            - Tente usar um modelo menor: `ollama pull llama3.2:3b` e altere o modelo no código
                            - Verifique se há outros processos usando muitos recursos
                            - Tente gerar menos questões por vez
                            - Certifique-se de que o Ollama está usando GPU (se disponível)
                            """)
                        except Exception as e:
                            st.error(f"❌ Erro ao gerar questionário: {str(e)}")
                            st.info("💡 Verifique se o Ollama está rodando e se o modelo está instalado corretamente.")
        
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
    
    # ========== GERENCIAR ALUNOS (PROFESSOR) ==========
    elif pagina_professor == "👥 Gerenciar Alunos":
        st.header("👥 Gerenciar Alunos")
        
        tab1, tab2 = st.tabs(["➕ Cadastrar Aluno", "📋 Lista de Alunos"])
        
        with tab1:
            st.subheader("Cadastrar Novo Aluno")
            
            with st.form("form_cadastrar_aluno_professor"):
                col1, col2 = st.columns(2)
                
                with col1:
                    nome_aluno = st.text_input("Nome Completo *", placeholder="Ex: João Silva")
                
                with col2:
                    matricula_aluno = st.text_input("Matrícula (opcional)", placeholder="Ex: 2024001")
                
                submitted = st.form_submit_button("✅ Cadastrar Aluno", type="primary")
                
                if submitted:
                    if not nome_aluno:
                        st.error("⚠️ O nome do aluno é obrigatório.")
                    else:
                        try:
                            aluno_id = st.session_state.db.criar_aluno(
                                nome=nome_aluno.strip(),
                                matricula=matricula_aluno.strip() if matricula_aluno else None
                            )
                            st.success(f"✅ Aluno cadastrado com sucesso! ID: {aluno_id}")
                            st.rerun()
                        except ValueError as e:
                            st.error(f"❌ {str(e)}")
                        except Exception as e:
                            st.error(f"❌ Erro ao cadastrar aluno: {str(e)}")
        
        with tab2:
            st.subheader("Alunos Cadastrados")
            
            alunos = st.session_state.db.listar_alunos()
            
            if not alunos:
                st.info("📝 Nenhum aluno cadastrado ainda. Use a aba 'Cadastrar Aluno' para adicionar alunos.")
            else:
                st.metric("Total de Alunos", len(alunos))
                st.divider()
                
                # Tabela de alunos
                dados_tabela = []
                for aluno in alunos:
                    dados_tabela.append({
                        'ID': aluno['id'],
                        'Nome': aluno['nome'],
                        'Matrícula': aluno['matricula'] if aluno['matricula'] else 'N/A',
                        'Data de Cadastro': aluno['data_cadastro']
                    })
                
                df_alunos = pd.DataFrame(dados_tabela)
                st.dataframe(df_alunos, use_container_width=True, hide_index=True)
                
                st.divider()
                st.subheader("🗑️ Excluir Aluno")
                
                aluno_opcoes = {f"{a['nome']} ({a['matricula'] if a['matricula'] else 'Sem matrícula'})": a['id'] 
                                for a in alunos}
                
                aluno_selecionado_excluir = st.selectbox(
                    "Selecione o aluno para excluir",
                    options=list(aluno_opcoes.keys())
                )
                
                if st.button("🗑️ Excluir Aluno", type="secondary"):
                    aluno_id_excluir = aluno_opcoes[aluno_selecionado_excluir]
                    if st.session_state.db.excluir_aluno(aluno_id_excluir):
                        st.success("✅ Aluno excluído com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao excluir aluno.")
    
    # ========== DASHBOARD (PROFESSOR) ==========
    elif pagina_professor == "📊 Dashboard":
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
                    'Matrícula': r.get('matricula_aluno', 'N/A'),
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

# Rodapé
st.sidebar.markdown("---")
st.sidebar.markdown("**PROFOCO v1.0**")
st.sidebar.markdown("Plataforma de Reforço Escolar")
st.sidebar.markdown("🔒 100% Local e Privado")
