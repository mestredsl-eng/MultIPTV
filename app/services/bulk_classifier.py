"""Bulk classification service for optimized database operations."""

from app.database import get_db
from app.services.parser import normalize_name, calculate_hash_midia
from app.services.classifier import classify_media, extract_season_episode, extract_year
from app.services.tmdb import get_movie_info
import logging

logger = logging.getLogger('process')


class BulkClassifier:
    """Optimized classifier with bulk database operations."""

    def __init__(self, batch_size=500, enable_tmdb=True):
        self.batch_size = batch_size
        self.enable_tmdb = enable_tmdb

    def process_iptv_source(self, iptv_source, cache_file_path):
        """Process all entries from a single IPTV source with bulk operations."""
        from app.services.parser import parse_m3u

        db = get_db()

        # Parse M3U file
        entries = parse_m3u(cache_file_path)
        logger.info(f"Processando {len(entries)} entradas de {iptv_source['nome']}")

        total_processed = 0
        total_skipped = 0

        # Batch processing
        batch_entries = []
        batch_hashes = []

        for i, entry in enumerate(entries):
            # Normalize name
            nome_normalizado = normalize_name(entry['name'])

            # C     k if quality upgrade is needed
                        score_atual = calcular_score_qualidade(
                                existing[4], existing[5]
                            ) ore_novo = calcular_score_qualidade(
                                e['qualidade'], e['tem_legendado'], e['has_hdr'], e['codec'], e['audio']
                            )
                            if score_novo > score_atual:
                                quality_upgrade_entries.append((e, existing[0], score_atual, score_novo))
                            # Update if category changed and no manual category
                            elif existing[2] != e['categoria']:
                                updated_entries.append(e)
                        else:
                            new_entries.append(e)
t 
                            (
                                e['iptv_id'], e['nome'], e['nome_normalizado'], e['url'],
                                e   e['ano'], e['season'], e['episode'], e['tmdb_id'],
                                e['qualidade'], e['tem_legendado']
                            )
                            for e in new_entries
                        ]

                        db.executemany('''
                            INSERT INTO midias (iptv_id, nome_da_midia, nome_normalizado, url, categoria,
                                              hash_midia, hash_base, origem_iptv, ano, season, episode, tmdb_id, 
                                  sra

                    # Quality upgrades
                    if quality_upgrade_entries:
                        for e, existing_id, score_atual, score_novo in quality_upgrade_entries:
                                UPDATE midias 
                                SET qualidade = ?, tem_legendado = ?, url = ?, ultima_atualizacao = CURRENT_TIMESTAMP
                                WHERE id = ?
                            ''', (e['qualidade'], e['tem_legendado'], e['url'], existing_id))
                            logger.info(f"Qualidade atualizada: {e['qualidade']} (score: {score_atual} → {score_novo})")
                        db.commit()

                    # Update entries with changed category
                    if updated_entries:
                        for e in updateash_midia = ?
                            ''', (e['categoria'], e['hash_midia']))
                        db.commit()

                    total_pre_
            # Clear batch
            batch_entries = []
                batch_hashes = [

                # Update pror': iptv_source['nome']
                }

        return {
            'total_processed': total_processed,
            'total_skipped': total_skip
        for iptv in iptv_sou:
            # Process this source
            for progress_update in self.process_iptv_source(dict(iptv), str(cache_file)):
                yield progress_update

            overall_processed += progress_update['processed']
            overall_skipped += progress_update['skipped']

        yield {
            'progress': 100,
            'processed': overall_processed,
            'skipped': overall_skipped,
            'complete': True
        }
