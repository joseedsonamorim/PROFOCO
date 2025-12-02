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
                respostas_json TEXT NOT NULL,
                nota REAL,
                analise_json TEXT,
                data_resposta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_questionario) REFERENCES questionarios(id)
            )
        """)
        
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
                        respostas: List[str], nota: float, analise: Dict) -> int:
        """Salva o resultado de um aluno"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        respostas_json = json.dumps(respostas, ensure_ascii=False)
        analise_json = json.dumps(analise, ensure_ascii=False)
        
        cursor.execute("""
            INSERT INTO resultados (id_questionario, nome_aluno, respostas_json, nota, analise_json)
            VALUES (?, ?, ?, ?, ?)
        """, (id_questionario, nome_aluno, respostas_json, nota, analise_json))
        
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
                   r.nome_aluno, r.respostas_json, r.nota, r.analise_json, r.data_resposta
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
                'respostas': json.loads(row[5]),
                'nota': row[6],
                'analise': json.loads(row[7]),
                'data_resposta': row[8]
            }
            for row in rows
        ]

