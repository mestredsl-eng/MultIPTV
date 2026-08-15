"""TMDB validation service with priority-based processing and automatic deduplication."""

import logging
import time
from app.database import get_db
from app.services.parser import count_words, normalize_name, remove_quality_indicators
from app.services.tmdb import get_movie_info

logger = logging.getLogger('process')


class TMDBValidatorService:
    """Service for TMDB validation with intelligent deduplication and name correction."""

    def __init__(self):
        self.quality_order = {
            '[L]': 10,  # Lossless/Melhor
            '4K': 9,
            'FHD': 8,
            'HD': 7,
            'SD': 6,
            '': 5,  # Sem qualidade definida
        }

    def get_quality_score(self, qualidade, nome):
        """Retorna o score de qualidade. Maior = melhor."""
        # Primeiro verificar o campo qualidade
        if qualidade:
            # Verificar se tem [L] no nome
            if '[L]' in qualidade:
                return self.quality_order['[L]']

            # Verificar outras qualidades
            for q, score in self.quality_order.items():
                if q and q in qualidade.upper():
                    return score

        # Se não tem qualidade definida, verificar no nome
        if nome:
            nome_upper = nome.upper()

            # Verificar [L] no nome
            if '[L]' in nome_upper:
                return self.quality_order['[L]']

            # Verificar outras qualidades no nome
            if '4K' in nome_upper:
                return self.quality_order['4K']
            if 'FHD' in nome_upper:
                return self.quality_order['FHD']
            if 'HD' in nome_upper:
                return self.quality_order['HD']
            if 'SD' in nome_upper:
                return self.quality_order['SD']

        return self.quality_order['']

    def validate_short_names(self):
        """Validate Movie items with ≤2 words (high priority)."""
        db = get_db()
        
        # Get all Movie items that need validation (≤2 words, no TMDB year)
        items = db.execute('''
            SELECT id, nome_da_midia, nome_normalizado, ano, tmdb_id, qualidade, black_list, status
            FROM midias 
            WHERE categoria = 'Movie' AND status = 1 AND black_list = 0
        ''').fetchall()
        
        # Filter by word count and priority
        items_to_validate = []
        for item in items:
            word_count = count_words(item['nome_da_midia'])
            if word_count <= 2 and item['ano'] is None:
                items_to_validate.append({
                    'id': item['id'],
                    'nome_da_midia': item['nome_da_midia'],
                    'nome_normalizado': item['nome_normalizado'],
                    'ano': item['ano'],
                    'tmdb_id': item['tmdb_id'],
                    'qualidade': item['qualidade'],
                    'word_count': word_count,
                    'priority': 1 if word_count == 1 else 2  # 1 word = highest priority
                })
        
        # Sort by priority (1 before 2)
        items_to_validate.sort(key=lambda x: x['priority'])
        
        logger.info(f"Found {len(items_to_validate)} Movie items with ≤2 words needing TMDB validation")
        
        return self._process_validation(items_to_validate, db)

    def validate_all_movies(self):
        """Validate all Movie items (normal priority)."""
        db = get_db()
        
        # Get all Movie items without TMDB validation
        items = db.execute('''
            SELECT id, nome_da_midia, nome_normalizado, ano, tmdb_id, qualidade, black_list, status
            FROM midias 
            WHERE categoria = 'Movie' AND status = 1 AND black_list = 0 AND (ano IS NULL OR tmdb_id IS NULL)
        ''').fetchall()
        
        items_to_validate = []
        for item in items:
            word_count = count_words(item['nome_da_midia'])
            items_to_validate.append({
                'id': item['id'],
                'nome_da_midia': item['nome_da_midia'],
                'nome_normalizado': item['nome_normalizado'],
                'ano': item['ano'],
                'tmdb_id': item['tmdb_id'],
                'qualidade': item['qualidade'],
                'word_count': word_count,
                'priority': word_count  # Lower word count = higher priority
            })
        
        # Sort by word count (ascending)
        items_to_validate.sort(key=lambda x: x['priority'])
        
        logger.info(f"Found {len(items_to_validate)} Movie items needing TMDB validation")
        
        return self._process_validation(items_to_validate, db)

    def _process_validation(self, items_to_validate, db):
        """Process validation with multiple attempts and deduplication."""
        validated_count = 0
        not_found_count = 0
        error_count = 0
        corrected_count = 0
        deduplicated_count = 0
        
        total = len(items_to_validate)
        
        # Check if there are items to validate
        if total == 0:
            logger.info("Nenhum item encontrado para validação")
            db.execute('''
                UPDATE process_status
                SET progresso = 100, mensagem = 'Nenhum item encontrado para validação', status = 'completed'
                WHERE status = 'running'
            ''')
            db.commit()
            return {
                'total': 0,
                'validated': 0,
                'not_found': 0,
                'errors': 0,
                'corrected': 0,
                'deduplicated': 0
            }
        
        logger.info(f"Iniciando validação de {total} itens...")
        
        for i, item in enumerate(items_to_validate):
            try:
                # Update progress more frequently (every item instead of every 10)
                progress = int((i + 1) / total * 100) if total > 0 else 0
                db.execute('''
                    UPDATE process_status
                    SET progresso = ?, mensagem = ?
                    WHERE status = 'running'
                ''', (progress, f'Validando {i + 1}/{total} itens ({validated_count} validados, {not_found_count} não encontrados)...'))
                db.commit()
                
                # Try multiple search variations
                tmdb_result = self._search_with_variations(item['nome_da_midia'], item['ano'], item['categoria'])
                
                if tmdb_result and tmdb_result.get('tmdb_id'):
                    # Found in TMDB - update database
                    validated_count += 1
                    
                    # Verify media type matches category to prevent incorrect corrections
                    tmdb_media_type = tmdb_result.get('media_type', 'movie')
                    expected_type = 'tv' if item['categoria'] in ['Series', 'Novela', 'Cartoon'] else 'movie'
                    
                    if tmdb_media_type != expected_type:
                        logger.warning(f"Media type mismatch: '{item['nome_da_midia']}' category '{item['categoria']}' but TMDB found as '{tmdb_media_type}' - skipping correction")
                        # Still update TMDB info but don't correct name
                        db.execute('''
                            UPDATE midias
                            SET tmdb_id = ?, ano = ?, ultima_atualizacao = CURRENT_TIMESTAMP
                            WHERE id = ?
                        ''', (tmdb_result['tmdb_id'], tmdb_result['year'], item['id']))
                        db.commit()
                    # Check if name needs correction
                    elif tmdb_result.get('title') != item['nome_da_midia']:
                        corrected_count += 1
                        new_nome = tmdb_result['title']
                        new_nome_normalizado = normalize_name(new_nome)
                        
                        # Update database with corrected name
                        db.execute('''
                            UPDATE midias
                            SET nome_da_midia = ?, nome_normalizado = ?, tmdb_id = ?, ano = ?, ultima_atualizacao = CURRENT_TIMESTAMP
                            WHERE id = ?
                        ''', (new_nome, new_nome_normalizado, tmdb_result['tmdb_id'], tmdb_result['year'], item['id']))
                        db.commit()
                        
                        logger.info(f"Name corrected: '{item['nome_da_midia']}' → '{new_nome}' (tmdb_id: {tmdb_result['tmdb_id']})")
                        
                        # Check for duplicates after correction
                        duplicates_removed = self.deduplicate_after_correction(item['id'], new_nome_normalizado, db)
                        deduplicated_count += duplicates_removed
                    else:
                        # Just update TMDB info without name change
                        db.execute('''
                            UPDATE midias
                            SET tmdb_id = ?, ano = ?, ultima_atualizacao = CURRENT_TIMESTAMP
                            WHERE id = ?
                        ''', (tmdb_result['tmdb_id'], tmdb_result['year'], item['id']))
                        db.commit()
                        
                        logger.info(f"TMDB validated: '{item['nome_da_midia']}' (tmdb_id: {tmdb_result['tmdb_id']}, year: {tmdb_result['year']})")
                else:
                    # Not found in TMDB - blacklist
                    not_found_count += 1
                    db.execute('''
                        UPDATE midias
                        SET black_list = 1, ultima_atualizacao = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (item['id'],))
                    db.commit()
                    
                    logger.warning(f"TMDB not found: '{item['nome_da_midia']}' - sent to blacklist")
                
                # Reduced rate limiting: 0.1s instead of 0.5s for faster processing
                # Also add progress update at the end
                if (i + 1) % 5 == 0:  # Every 5 items, update with detailed status
                    progress = int((i + 1) / total * 100) if total > 0 else 0
                    db.execute('''
                        UPDATE process_status
                        SET progresso = ?, mensagem = ?
                        WHERE status = 'running'
                    ''', (progress, f'Validando {i + 1}/{total} itens ({validated_count} validados, {not_found_count} não encontrados, {corrected_count} corrigidos)...'))
                    db.commit()
                
                time.sleep(0.1)
                
            except Exception as e:
                error_count += 1
                logger.error(f"Error validating '{item['nome_da_midia']}': {e}")
                continue
        
        # Final deduplication scan
        final_dedup = self.final_deduplication(db)
        deduplicated_count += final_dedup
        
        return {
            'total': total,
            'validated': validated_count,
            'not_found': not_found_count,
            'errors': error_count,
            'corrected': corrected_count,
            'deduplicated': deduplicated_count
        }

    def _search_with_variations(self, nome, year=None, categoria=None):
        """Search TMDB with multiple name variations and year filtering."""
        variations = [
            (nome, year),  # Original with year if provided
            (remove_quality_indicators(nome), year),  # Without quality, with year
        ]
        
        # Remove year if present (for another variation without year)
        import re
        year_pattern = re.compile(r'\s*[\(\[]?\d{4}[\)\]]?\s*')
        nome_no_year = year_pattern.sub(' ', nome).strip()
        if nome_no_year != nome:
            variations.append((nome_no_year, None))  # Without year
        
        # Try each variation
        for variation_nome, variation_year in variations:
            if variation_nome and len(variation_nome) > 2:  # Skip very short names
                try:
                    result = get_movie_info(variation_nome, variation_year, categoria)
                    if result and result.get('tmdb_id'):
                        return result
                except Exception as e:
                    logger.warning(f"Error searching TMDB for '{variation_nome}': {e}")
                    continue  # Try next variation
        
        return None

    def deduplicate_after_correction(self, media_id, new_nome_normalizado, db):
        """Check and remove duplicates after name correction."""
        # Find duplicates by the new normalized name
        duplicates = db.execute('''
            SELECT id, nome_da_midia, qualidade, tmdb_id, black_list
            FROM midias
            WHERE nome_normalizado = ? AND id != ? AND categoria = 'Movie' AND status = 1
        ''', (new_nome_normalizado, media_id)).fetchall()
        
        if not duplicates:
            return 0
        
        removed_count = 0
        
        for dup in duplicates:
            # Get original item for comparison
            original = db.execute('''
                SELECT id, nome_da_midia, qualidade, tmdb_id, black_list
                FROM midias
                WHERE id = ?
            ''', (media_id,)).fetchone()
            
            if not original:
                continue
            
            # Apply deduplication logic
            decision = self._deduplication_decision(original, dup)
            
            if decision['keep'] == 'original':
                # Blacklist the duplicate
                db.execute('''
                    UPDATE midias
                    SET black_list = 1, ultima_atualizacao = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (dup['id'],))
                db.commit()
                
                logger.info(f"Duplication detected: Keeping ID {media_id} ({original['nome_da_midia']}, {decision['reason']}), sending ID {dup['id']} to blacklist")
                removed_count += 1
            else:
                # Blacklist the original (rare case)
                db.execute('''
                    UPDATE midias
                    SET black_list = 1, ultima_atualizacao = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (media_id,))
                db.commit()
                
                logger.info(f"Duplication detected: Keeping ID {dup['id']} ({dup['nome_da_midia']}, {decision['reason']}), sending ID {media_id} to blacklist")
                removed_count += 1
        
        return removed_count

    def final_deduplication(self, db):
        """Final deduplication scan after all validations."""
        # Find all duplicate groups
        duplicate_groups = db.execute('''
            SELECT nome_normalizado, COUNT(*) as count
            FROM midias
            WHERE categoria = 'Movie' AND status = 1 AND black_list = 0
            GROUP BY nome_normalizado
            HAVING count > 1
        ''').fetchall()
        
        removed_count = 0
        
        for group in duplicate_groups:
            nome_normalizado = group['nome_normalizado']
            
            # Get all items in this group
            items = db.execute('''
                SELECT id, nome_da_midia, qualidade, tmdb_id, black_list
                FROM midias
                WHERE nome_normalizado = ? AND categoria = 'Movie' AND status = 1 AND black_list = 0
                ORDER BY id
            ''', (nome_normalizado,)).fetchall()
            
            if len(items) < 2:
                continue
            
            # Keep the best one, blacklist the rest
            best_item = items[0]
            for item in items[1:]:
                decision = self._deduplication_decision(best_item, item)
                
                if decision['keep'] == 'original':
                    # Blacklist this item
                    db.execute('''
                        UPDATE midias
                        SET black_list = 1, ultima_atualizacao = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (item['id'],))
                    db.commit()
                    removed_count += 1
                else:
                    # This item is better, blacklist the previous best
                    db.execute('''
                        UPDATE midias
                        SET black_list = 1, ultima_atualizacao = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (best_item['id'],))
                    db.commit()
                    removed_count += 1
                    best_item = item  # This becomes the new best
        
        if removed_count > 0:
            logger.info(f"Final deduplication: {removed_count} duplicates removed")
        
        return removed_count

    def _deduplication_decision(self, item1, item2):
        """Decide which item to keep based on quality and TMDB validation."""
        # Case 1: One has TMDB validation, other doesn't
        has_tmdb_1 = item1['tmdb_id'] is not None
        has_tmdb_2 = item2['tmdb_id'] is not None
        
        if has_tmdb_1 and not has_tmdb_2:
            return {'keep': 'original', 'reason': 'has TMDB validation'}
        if has_tmdb_2 and not has_tmdb_1:
            return {'keep': 'duplicate', 'reason': 'has TMDB validation'}
        
        # Case 2: Both have TMDB validation or neither - use quality
        score_1 = self.get_quality_score(item1['qualidade'], item1['nome_da_midia'])
        score_2 = self.get_quality_score(item2['qualidade'], item2['nome_da_midia'])
        
        if score_1 > score_2:
            return {'keep': 'original', 'reason': f'better quality (score: {score_1} vs {score_2})'}
        elif score_2 > score_1:
            return {'keep': 'duplicate', 'reason': f'better quality (score: {score_2} vs {score_1})'}
        else:
            # Same quality - keep the older one (lower ID)
            if item1['id'] < item2['id']:
                return {'keep': 'original', 'reason': 'older entry'}
            else:
                return {'keep': 'duplicate', 'reason': 'older entry'}

    def blacklist_unvalidated(self):
        """Send non-validated items to blacklist."""
        db = get_db()
        
        # Find Movie items with ≤2 words and no TMDB validation
        items = db.execute('''
            SELECT id, nome_da_midia
            FROM midias
            WHERE categoria = 'Movie' AND status = 1 AND black_list = 0 
            AND (ano IS NULL OR tmdb_id IS NULL)
        ''').fetchall()
        
        blacklisted_count = 0
        
        for item in items:
            word_count = count_words(item['nome_da_midia'])
            if word_count <= 2:
                db.execute('''
                    UPDATE midias
                    SET black_list = 1, ultima_atualizacao = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (item['id'],))
                blacklisted_count += 1
        
        db.commit()
        
        logger.info(f"Blacklisted {blacklisted_count} unvalidated items")
        
        return {'blacklisted': blacklisted_count}

    def get_validation_stats(self):
        """Get validation statistics."""
        db = get_db()
        
        stats = {
            'movies_total': db.execute("SELECT COUNT(*) FROM midias WHERE categoria = 'Movie' AND status = 1").fetchone()[0],
            'movies_needing_validation': 0,
            'movies_validated': 0,
            'movies_not_found': 0
        }
        
        # Count movies needing validation (≤2 words, no TMDB)
        items = db.execute('''
            SELECT nome_da_midia, ano, tmdb_id
            FROM midias
            WHERE categoria = 'Movie' AND status = 1 AND black_list = 0
        ''').fetchall()
        
        for item in items:
            word_count = count_words(item['nome_da_midia'])
            if word_count <= 2 and item['ano'] is None:
                stats['movies_needing_validation'] += 1
            elif item['tmdb_id'] is not None:
                stats['movies_validated'] += 1
        
        # Count blacklisted (not found)
        stats['movies_not_found'] = db.execute('''
            SELECT COUNT(*) FROM midias 
            WHERE categoria = 'Movie' AND status = 1 AND black_list = 1
        ''').fetchone()[0]
        
        return stats