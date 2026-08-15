"""Database models for ORM-like access."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Iptv:
    id: int
    nome: str
    url_m3u: str
    url_epg: str
    ativo: bool
    data_cadastro: datetime
    ultima_atualizacao: datetime = None


@dataclass
class Midia:
    id: int
    iptv_id: int
    nome_da_midia: str
    nome_normalizado: str
    url: str
    local_da_galeria: str = None
    qualidade: str = None
    imagem_url: str = None
    categoria: str = None
    black_list: bool = False
    status: bool = True
    id_externo: str = None
    hash_midia: str = None
    origem_iptv: str = None
    ano: int = None
    season: int = None
    episode: int = None
    tmdb_id: int = None
    data_coleta: datetime = None
    data_processamento: datetime = None
    ultima_atualizacao: datetime = None


@dataclass
class TvChannel:
    id: int
    iptv_id: int
    nome_canal: str
    nome_normalizado: str
    url: str
    logo_url: str = None
    categoria: str = None
    black_list: bool = False
    status: bool = True
    id_externo: str = None
    hash_canal: str = None
    qualidade: str = None
    tvg_id: str = None
    data_coleta: datetime = None
    data_processamento: datetime = None
    ultima_atualizacao: datetime = None


@dataclass
class TmdbCache:
    tmdb_id: int
    titulo: str
    titulo_normalizado: str
    ano: int = None
    tipo: str = None
    poster: str = None
    backdrop: str = None
    json: str = None
    ultima_consulta: datetime = None


@dataclass
class ExportedMedia:
    id: int
    hash_midia: str
    arquivo: str
    ultima_exportacao: datetime = None
    hash_arquivo: str = None


@dataclass
class ExportLock:
    id: int
    locked: bool
    locked_since: datetime = None
    locked_by: str = None
    ultimo_heartbeat: datetime = None


@dataclass
class ProcessStatus:
    id: int
    etapa: str
    progresso: int = 0
    mensagem: str = None
    inicio: datetime = None
    fim: datetime = None
    status: str = 'pending'


@dataclass
class FilaProcessamento:
    id: int
    etapa: str
    inicio: datetime = None
    fim: datetime = None
    status: str = 'pending'


@dataclass
class ExecutionStats:
    id: int
    tipo_execucao: str
    inicio: datetime = None
    fim: datetime = None
    duracao_segundos: int = None
    itens_novos: int = 0
    itens_ignorados: int = 0
    itens_exportados: int = 0
    status: str = 'pending'


@dataclass
class SystemSetting:
    chave: str
    valor: str
    descricao: str = None
    ultima_atualizacao: datetime = None
