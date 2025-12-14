"""
Módulo de gerenciamento do banco de dados SQLite
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional


class Database:
    def __init__(self, db_path: str = "profoco.db"):
        """Inicializa a conexão com o banco de dados e cria as tabelas"""
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Retorna uma conexão com o banco de dados"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Cria as tabelas necessárias se não existirem"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabela de alunos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alunos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                matricula TEXT UNIQUE,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de questionários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questionarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                disciplina TEXT NOT NULL,
                topico TEXT NOT NULL,
                questoes_json TEXT NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de resultados
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resultados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_questionario INTEGER NOT NULL,
                nome_aluno TEXT NOT NULL,
                matricula_aluno TEXT,
                respostas_json TEXT NOT NULL,
                nota REAL,
                analise_json TEXT,
                data_resposta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_questionario) REFERENCES questionarios(id)
            )
        """)
        
        # Migração: adiciona coluna matricula_aluno se não existir (para bancos antigos)
        try:
            cursor.execute("ALTER TABLE resultados ADD COLUMN matricula_aluno TEXT")
        except sqlite3.OperationalError:
            # Coluna já existe, ignora
            pass
        
        conn.commit()
        conn.close()
    
    def criar_questionario(self, disciplina: str, topico: str, questoes: List[Dict]) -> int:
        """Salva um novo questionário no banco de dados"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        questoes_json = json.dumps(questoes, ensure_ascii=False)
        
        cursor.execute("""
            INSERT INTO questionarios (disciplina, topico, questoes_json)
            VALUES (?, ?, ?)
        """, (disciplina, topico, questoes_json))
        
        questionario_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return questionario_id
    
    def obter_questionario(self, questionario_id: int) -> Optional[Dict]:
        """Obtém um questionário pelo ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, disciplina, topico, questoes_json, data_criacao
            FROM questionarios
            WHERE id = ?
        """, (questionario_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'disciplina': row[1],
                'topico': row[2],
                'questoes': json.loads(row[3]),
                'data_criacao': row[4]
            }
        return None
    
    def listar_questionarios(self) -> List[Dict]:
        """Lista todos os questionários"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, disciplina, topico, data_criacao
            FROM questionarios
            ORDER BY data_criacao DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'disciplina': row[1],
                'topico': row[2],
                'data_criacao': row[3]
            }
            for row in rows
        ]
    
    def salvar_resultado(self, id_questionario: int, nome_aluno: str, 
                        respostas: List[str], nota: float, analise: Dict,
                        matricula_aluno: Optional[str] = None) -> int:
        """Salva o resultado de um aluno"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        respostas_json = json.dumps(respostas, ensure_ascii=False)
        analise_json = json.dumps(analise, ensure_ascii=False)
        
        cursor.execute("""
            INSERT INTO resultados (id_questionario, nome_aluno, matricula_aluno, respostas_json, nota, analise_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (id_questionario, nome_aluno, matricula_aluno, respostas_json, nota, analise_json))
        
        resultado_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return resultado_id
    
    def obter_resultados_questionario(self, id_questionario: int) -> List[Dict]:
        """Obtém todos os resultados de um questionário"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, nome_aluno, respostas_json, nota, analise_json, data_resposta
            FROM resultados
            WHERE id_questionario = ?
            ORDER BY data_resposta DESC
        """, (id_questionario,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'nome_aluno': row[1],
                'respostas': json.loads(row[2]),
                'nota': row[3],
                'analise': json.loads(row[4]),
                'data_resposta': row[5]
            }
            for row in rows
        ]
    
    def obter_todos_resultados(self) -> List[Dict]:
        """Obtém todos os resultados de todos os questionários"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT r.id, r.id_questionario, q.disciplina, q.topico, 
                   r.nome_aluno, r.matricula_aluno, r.respostas_json, r.nota, r.analise_json, r.data_resposta
            FROM resultados r
            JOIN questionarios q ON r.id_questionario = q.id
            ORDER BY r.data_resposta DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'id_questionario': row[1],
                'disciplina': row[2],
                'topico': row[3],
                'nome_aluno': row[4],
                'matricula_aluno': row[5],
                'respostas': json.loads(row[6]),
                'nota': row[7],
                'analise': json.loads(row[8]),
                'data_resposta': row[9]
            }
            for row in rows
        ]
    
    def criar_aluno(self, nome: str, matricula: Optional[str] = None) -> int:
        """Cria um novo aluno no banco de dados"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Verifica se já existe aluno com mesmo nome ou matrícula
        if matricula:
            cursor.execute("SELECT id FROM alunos WHERE matricula = ?", (matricula,))
            if cursor.fetchone():
                conn.close()
                raise ValueError(f"Já existe um aluno com a matrícula {matricula}")
        
        cursor.execute("SELECT id FROM alunos WHERE nome = ?", (nome,))
        if cursor.fetchone():
            conn.close()
            raise ValueError(f"Já existe um aluno com o nome {nome}")
        
        cursor.execute("""
            INSERT INTO alunos (nome, matricula)
            VALUES (?, ?)
        """, (nome, matricula))
        
        aluno_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return aluno_id
    
    def autenticar_aluno(self, identificador: str) -> Optional[Dict]:
        """Autentica um aluno por nome ou matrícula"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tenta encontrar por matrícula ou nome
        cursor.execute("""
            SELECT id, nome, matricula, data_cadastro
            FROM alunos
            WHERE matricula = ? OR nome = ?
        """, (identificador, identificador))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'nome': row[1],
                'matricula': row[2],
                'data_cadastro': row[3]
            }
        return None
    
    def listar_alunos(self) -> List[Dict]:
        """Lista todos os alunos cadastrados"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, nome, matricula, data_cadastro
            FROM alunos
            ORDER BY nome ASC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'nome': row[1],
                'matricula': row[2],
                'data_cadastro': row[3]
            }
            for row in rows
        ]
    
    def excluir_aluno(self, aluno_id: int) -> bool:
        """Exclui um aluno do banco de dados"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM alunos WHERE id = ?", (aluno_id,))
            conn.commit()
            deleted = cursor.rowcount > 0
            conn.close()
            return deleted
        except Exception:
            conn.close()
            return False
    
    def obter_resultados_aluno(self, nome_aluno: Optional[str] = None, 
                               matricula: Optional[str] = None) -> List[Dict]:
        """Obtém todos os resultados de um aluno específico"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if matricula:
            cursor.execute("""
                SELECT r.id, r.id_questionario, q.disciplina, q.topico, 
                       r.nome_aluno, r.matricula_aluno, r.respostas_json, r.nota, r.analise_json, r.data_resposta
                FROM resultados r
                JOIN questionarios q ON r.id_questionario = q.id
                WHERE r.matricula_aluno = ?
                ORDER BY r.data_resposta DESC
            """, (matricula,))
        elif nome_aluno:
            cursor.execute("""
                SELECT r.id, r.id_questionario, q.disciplina, q.topico, 
                       r.nome_aluno, r.matricula_aluno, r.respostas_json, r.nota, r.analise_json, r.data_resposta
                FROM resultados r
                JOIN questionarios q ON r.id_questionario = q.id
                WHERE r.nome_aluno = ?
                ORDER BY r.data_resposta DESC
            """, (nome_aluno,))
        else:
            conn.close()
            return []
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'id_questionario': row[1],
                'disciplina': row[2],
                'topico': row[3],
                'nome_aluno': row[4],
                'matricula_aluno': row[5],
                'respostas': json.loads(row[6]),
                'nota': row[7],
                'analise': json.loads(row[8]),
                'data_resposta': row[9]
            }
            for row in rows
        ]

