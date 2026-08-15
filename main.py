"""
Script principal do IPTV Jellyfin Manager (CLI)
Fluxo automatizado para gerenciar listas IPTV
Nota: Este script é compatível com o projeto original iptv_manager
Para uso via web, utilize a aplicação Flask em run.py
"""
import sys
import logging
from pathlib import Path

# Adicionar diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Verificar se deve rodar em modo automático (sem perguntas)
AUTO_MODE = '--auto' in sys.argv or '-a' in sys.argv

# Verificar flags de modo incremental
FULL_MODE = '--full' in sys.argv or '--no-incremental' in sys.argv
CLEAR_PROCESSED = '--clear-processed' in sys.argv
STATS_ONLY = '--stats-only' in sys.argv

# Configurar logger para o script principal
logger = logging.getLogger(__name__)

try:
    from iptv_manager.config import TMDB_API_KEY
    from iptv_manager.database import init_database, add_iptv_source, get_iptv_sources, add_channel, add_channels_batch
    from iptv_manager.downloader import download_all_m3u, cleanup_cache
    from iptv_manager.parser import parse_all_m3u, normalize_channel_name
    from iptv_manager.classifier import classify_entries, learn_keywords
    from iptv_manager.deduplicator import deduplicate_all, filter_unwanted_categories
    from iptv_manager.tmdb_client import init_tmdb, enrich_movies_with_tmdb
    from iptv_manager.strm_generator import generate_all_strm
    from iptv_manager.m3u_generator import generate_tv_m3u
    from iptv_manager.utils import filter_out_ts
    from iptv_manager.database import get_processed_entries_count, clear_processed_entries, mark_entries_processed
    from iptv_manager.epg_fetcher import download_epg_file, DEFAULT_EPG_SOURCES
    from iptv_manager.config import OUTPUT_DIR
except ImportError as e:
    print(f"Erro: Não foi possível importar módulos do iptv_manager: {e}")
    print("Este script CLI requer o projeto original iptv_manager.")
    print("Para uso via web, execute: python run.py")
    sys.exit(1)

def ask_add_iptv():
    """Pergunta se o usuário quer adicionar uma nova fonte IPTV"""
    if AUTO_MODE:
        # Em modo automático, verifica se há fontes existentes
        print("\n=== IPTV Jellyfin Manager (Modo Automático) ===")
        sources = get_iptv_sources()
        if not sources:
            print("Nenhuma fonte IPTV cadastrada.")
            print("Adicione uma fonte IPTV executando o script sem --auto ou configurando via banco de dados.")
            return None
        else:
            print(f"Usando {len(sources)} fonte(s) IPTV existente(s)...")
            return None
    
    print("\n=== IPTV Jellyfin Manager ===")
    response = input("Deseja adicionar uma nova fonte IPTV? (s/n): ").strip().lower()
    
    if response == 's':
        url = input("Digite a URL do M3U: ").strip()
        name = input("Digite um nome para esta fonte (opcional): ").strip()
        
        if url:
            source_id = add_iptv_source(url, name if name else None)
            print(f"Fonte IPTV adicionada com ID: {source_id}")
            return source_id
    
    return None

def main():
    """Fluxo principal automatizado"""
    try:
        print("Iniciando IPTV Jellyfin Manager...")
        
        # Inicializar banco de dados
        print("Inicializando banco de dados...")
        init_database()
        
        # Modo incremental: processar apenas novidades (pode ser desativado com --full)
        incremental = not FULL_MODE
        
        # Limpar cache antigo
        print("Limpando cache antigo...")
        try:
            cleanup_cache(max_age_hours=24)
        except Exception as e:
            print(f"  Aviso: Erro ao limpar cache: {e}")
        
        # Inicializar TMDB (obrigatório)
        print("Inicializando TMDB...")
        try:
            init_tmdb()
        except Exception as e:
            print(f"  Erro ao inicializar TMDB: {e}")
            print("  O sistema continuará sem enriquecimento TMDB.")
        
        # Perguntar se quer adicionar nova fonte IPTV
        ask_add_iptv()
        
        # Verificar se há fontes IPTV
        sources = get_iptv_sources(active_only=True)
        
        if not sources:
            print("Nenhuma fonte IPTV cadastrada. Adicione uma fonte para continuar.")
            return
        
        print(f"\nProcessando {len(sources)} fonte(s) IPTV...")
        
        # Limpar histórico de entradas processadas se solicitado
        if CLEAR_PROCESSED:
            print("Limpando histórico de entradas processadas...")
            try:
                clear_processed_entries()
                print("  Histórico limpo com sucesso!")
            except Exception as e:
                print(f"  Erro ao limpar histórico: {e}")
                return
        
        # Mostrar estatísticas de processamento anterior
        try:
            processed_count = get_processed_entries_count()
            if incremental:
                print(f"Modo incremental: {processed_count} entradas já processadas serão puladas")
            else:
                print(f"Modo completo: Todas as entradas serão processadas ({processed_count} no histórico)")
        except Exception as e:
            print(f"  Aviso: Erro ao obter estatísticas: {e}")
        
        # Se apenas estatísticas, mostrar e sair
        if STATS_ONLY:
            print("\n=== Estatísticas do Processamento ===")
            try:
                from iptv_manager.database import get_content_by_source
                sources = get_iptv_sources(active_only=True)
                for source in sources:
                    content = get_content_by_source(source['id'])
                    print(f"\nFonte: {source['name'] or source['url']}")
                    print(f"  Canais: {len(content.get('channels', []))}")
                    print(f"  Filmes: {len(content.get('movies', []))}")
                    print(f"  Séries: {len(content.get('series', []))}")
                    print(f"  Desenhos: {len(content.get('cartoons', []))}")
                    print(f"  Esportes: {len(content.get('sports', []))}")
                    print(f"  Educacional: {len(content.get('educational', []))}")
                    print(f"  Documentários: {len(content.get('documentaries', []))}")
                    print(f"  Novelas: {len(content.get('novels', []))}")
                    print(f"  Adulto: {len(content.get('adult', []))}")
                print(f"\nTotal de entradas processadas: {get_processed_entries_count()}")
            except Exception as e:
                print(f"  Erro ao obter estatísticas: {e}")
            return
        
        # Baixar/atualizar M3Us
        print("\n1. Baixando/atualizando arquivos M3U...")
        downloaded_files = download_all_m3u()
        
        if not downloaded_files:
            print("Nenhum arquivo M3U foi baixado.")
            return
        
        # Parsear M3Us
        print("\n2. Parseando arquivos M3U...")
        try:
            all_entries = parse_all_m3u(downloaded_files, incremental=incremental)
        except Exception as e:
            print(f"  Erro ao parsear M3Us: {e}")
            return
        
        # Combinar todas as entradas
        all_entries_list = []
        for source_id, entries in all_entries.items():
            all_entries_list.extend(entries)
        
        print(f"Total de entradas encontradas: {len(all_entries_list)}")
        
        # Classificar conteúdo
        print("\n3. Classificando conteúdo...")
        try:
            classified = classify_entries(all_entries_list)
        except Exception as e:
            print(f"  Erro ao classificar conteúdo: {e}")
            return
        
        # Aprender palavras-chave
        print("4. Aprendendo padrões de nomenclatura...")
        try:
            learn_keywords(all_entries_list)
        except Exception as e:
            print(f"  Aviso: Erro ao aprender palavras-chave: {e}")
        
        # Remover duplicatas
        print("\n5. Removendo duplicatas...")
        try:
            deduplicated = deduplicate_all(classified)
        except Exception as e:
            print(f"  Erro ao remover duplicatas: {e}")
            deduplicated = classified
        
        # Filtrar categorias indesejadas (Religious, Music)
        print("\n6. Filtrando categorias indesejadas...")
        try:
            filtered = filter_unwanted_categories(deduplicated)
        except Exception as e:
            print(f"  Erro ao filtrar categorias: {e}")
            filtered = deduplicated
        
        # Enriquecer filmes com TMDB (obrigatório)
        if 'Movie' in filtered:
            print("\n7. Enriquecendo filmes com TMDB...")
            print(f"  Total de filmes para enriquecer: {len(filtered['Movie'])}")
            try:
                filtered['Movie'] = enrich_movies_with_tmdb(filtered['Movie'])
            except Exception as e:
                print(f"  Aviso: Erro ao enriquecer filmes com TMDB: {e}")
        
        # Filtrar .ts de categorias não-TV (Movies, Series, etc.)
        # TS deve ser apenas para TV ao vivo
        non_tv_categories = ['Movie', 'Series', 'Cartoon', 'Documentary', 'Novel', 'Educational', 'Adult', 'Sports']
        for category in non_tv_categories:
            if category in filtered:
                print(f"\n8. Removendo streams .ts de {category}...")
                try:
                    before_count = len(filtered[category])
                    filtered[category] = filter_out_ts(filtered[category])
                    after_count = len(filtered[category])
                    removed = before_count - after_count
                    if removed > 0:
                        print(f"  Removidos {removed} streams .ts de {category}")
                except Exception as e:
                    print(f"  Aviso: Erro ao filtrar {category}: {e}")
        
        # Gerar arquivos .strm
        print("\n9. Gerando arquivos .strm...")
        try:
            for file_info in downloaded_files:
                generate_all_strm(filtered, file_info['source_id'])
        except Exception as e:
            print(f"  Erro ao gerar arquivos .strm: {e}")
        
        # Gerar tv.m3u
        if 'TV' in filtered:
            print("\n10. Gerando tv.m3u...")
            try:
                tv_channels = filtered['TV']
                # Passar URL do EPG para o M3U (Jellyfin usa isso para guia)
                # Usar arquivo local EPG já baixado para Jellyfin
                epg_url = "epg.xml"
                generate_tv_m3u(tv_channels, epg_url=epg_url)
            except Exception as e:
                print(f"  Erro ao gerar tv.m3u: {e}")
        
        # Baixar EPG
        print("\n11. Baixando EPG...")
        try:
            if DEFAULT_EPG_SOURCES:
                epg_output_path = OUTPUT_DIR / "TV" / "epg.xml"
                for epg_source in DEFAULT_EPG_SOURCES:
                    success = download_epg_file(epg_source, epg_output_path)
                    if success:
                        break
            else:
                print("  Aviso: Nenhuma fonte de EPG configurada")
        except Exception as e:
            print(f"  Erro ao baixar EPG: {e}")
        
        # Marcar entradas como processadas (sempre, exceto em modo full)
        # IMPORTANTE: Canais de TV NÃO são marcados como processados para garantir tv.m3u completo
        if incremental:
            print("\n11. Marcando entradas como processadas (exceto TV)...")
            try:
                entries_to_mark = []
                tv_count = 0
                for category, entries in filtered.items():
                    for entry in entries:
                        url_hash = entry.get('url_hash')
                        url = entry.get('url', '')
                        source_id = entry.get('iptv_source_id', 0)
                        # NÃO marcar canais de TV como processados
                        if url_hash and category != 'TV':
                            entries_to_mark.append({
                                'url_hash': url_hash,
                                'url': url,
                                'category': category,
                                'iptv_source_id': source_id
                            })
                        elif category == 'TV':
                            tv_count += 1
                
                # Usar batch operation para marcar todas as entradas
                if entries_to_mark:
                    mark_entries_processed(entries_to_mark)
                    print(f"  Marcadas {len(entries_to_mark)} entradas como processadas")
                    print(f"  {tv_count} canais de TV não foram marcados (sempre reprocessados)")
            except Exception as e:
                print(f"  Aviso: Erro ao marcar entradas como processadas: {e}")
        
        print("\n=== Processamento concluído! ===")
        print(f"Modo de execução: {'INCREMENTAL' if incremental else 'COMPLETO'}")
        print(f"Total de canais de TV: {len(filtered.get('TV', []))}")
        print(f"Total de filmes: {len(filtered.get('Movie', []))}")
        print(f"Total de séries: {len(filtered.get('Series', []))}")
        print(f"Total de desenhos: {len(filtered.get('Cartoon', []))}")
        print(f"Total de esportes: {len(filtered.get('Sports', []))}")
        print(f"Total de educacional: {len(filtered.get('Educational', []))}")
        print(f"Total de documentários: {len(filtered.get('Documentary', []))}")
        print(f"Total de novelas: {len(filtered.get('Novel', []))}")
        print(f"Total de conteúdo adulto: {len(filtered.get('Adult', []))}")
        
        if incremental:
            try:
                total_processed = get_processed_entries_count()
                print(f"\nTotal de entradas processadas acumuladas: {total_processed}")
            except Exception as e:
                print(f"  Aviso: Erro ao obter total processado: {e}")
    
    except KeyboardInterrupt:
        print("\n\nProcessamento interrompido pelo usuário.")
    except Exception as e:
        print(f"\n\nERRO FATAL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
