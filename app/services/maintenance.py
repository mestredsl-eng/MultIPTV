"""Maintenance service for database cleanup and deduplication."""

import re
from app.database import get_db
from app.services.parser import normalize_name


class MaintenanceService:
    """Service for database maintenance operations."""

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

    def fix_duplicates_by_name(self):
        """Corrige duplicatas por nome normalizado."""
        db = get_db()

        # Buscar todas as mídias ativas
        items = db.execute('''
            SELECT id, nome_da_midia, nome_normalizado, black_list
            FROM midias
            WHERE status = 1
            ORDER BY nome_normalizado
        ''').fetchall()

        # Agrupar por nome normalizado
        name_groups = {}
        for item in items:
            media_id, nome, nome_normalizado, black_list = item
            key = nome_normalizado or nome.lower()
            if key not in name_groups:
                name_groups[key] = []
            name_groups[key].append({
                'id': media_id,
                'nome': nome,
                'nome_normalizado': nome_normalizado,
                'black_list': black_list
            })

        # Encontrar grupos com duplicados
        duplicate_groups = {k: v for k, v in name_groups.items() if len(v) > 1}

        # Processar cada grupo
        total_to_blacklist = 0
        processed_count = 0

        for name, group in duplicate_groups.items():
            # Ordenar por ID para manter o mais antigo como original
            group.sort(key=lambda x: x['id'])

            # Manter o primeiro como original, marcar outros como blacklist
            original = group[0]
            duplicates = group[1:]

            for dup in duplicates:
                if dup['black_list'] == 0:  # Só marcar se não estiver já em blacklist
                    db.execute('UPDATE midias SET black_list = 1 WHERE id = ?', (dup['id'],))
                    total_to_blacklist += 1

            processed_count += 1

        db.commit()

        return {
            'processed_groups': processed_count,
            'blacklisted_items': total_to_blacklist
        }

    def fix_quality_duplicates(self):
        """Corrige duplicatas mantendo apenas a melhor qualidade."""
        db = get_db()

        # Buscar todas as mídias ativas
        items = db.execute('''
            SELECT id, nome_da_midia, nome_normalizado, qualidade, black_list
            FROM midias
            WHERE status = 1
            ORDER BY nome_normalizado
        ''').fetchall()

        # Agrupar por nome normalizado
        name_groups = {}
        for item in items:
            media_id, nome, nome_normalizado, qualidade, black_list = item
            key = nome_normalizado or nome.lower()
            if key not in name_groups:
                name_groups[key] = []
            name_groups[key].append({
                'id': media_id,
                'nome': nome,
                'nome_normalizado': nome_normalizado,
                'qualidade': qualidade,
                'black_list': black_list,
                'quality_score': self.get_quality_score(qualidade, nome)
            })

        # Encontrar grupos com múltiplas qualidades
        multi_quality_groups = {k: v for k, v in name_groups.items() if len(v) > 1}

        # Processar cada grupo
        total_to_blacklist = 0
        total_kept = 0
        processed_count = 0

        for name, group in multi_quality_groups.items():
            # Ordenar por score de qualidade (decrescente)
            group.sort(key=lambda x: x['quality_score'], reverse=True)

            # Manter apenas o melhor
            best = group[0]
            others = group[1:]

            total_kept += 1

            for item in others:
                if item['black_list'] == 0:  # Só marcar se não estiver já em blacklist
                    db.execute('UPDATE midias SET black_list = 1 WHERE id = ?', (item['id'],))
                    total_to_blacklist += 1

            processed_count += 1

        db.commit()

        return {
            'processed_groups': processed_count,
            'kept_items': total_kept,
            'blacklisted_items': total_to_blacklist
        }

    def cleanup_orphaned_records(self):
        """Remove registros órfãos (sem IPTV source ativo)."""
        db = get_db()

        # Remove mídias de IPTVs desativados
        result = db.execute('''
            UPDATE midias
            SET status = 0
            WHERE iptv_id IN (SELECT id FROM iptvs WHERE ativo = 0)
        ''')
        media_count = result.rowcount

        # Remove canais TV de IPTVs desativados
        result = db.execute('''
            UPDATE tv_channels
            SET status = 0
            WHERE iptv_id IN (SELECT id FROM iptvs WHERE ativo = 0)
        ''')
        tv_count = result.rowcount

        db.commit()

        return {
            'media_deactivated': media_count,
            'tv_deactivated': tv_count
        }

    def get_statistics(self):
        """Retorna estatísticas de manutenção."""
        db = get_db()

        stats = {
            'total_midias': db.execute('SELECT COUNT(*) FROM midias WHERE status = 1').fetchone()[0],
            'total_tv_channels': db.execute('SELECT COUNT(*) FROM tv_channels WHERE status = 1').fetchone()[0],
            'blacklisted_midias': db.execute('SELECT COUNT(*) FROM midias WHERE black_list = 1 AND status = 1').fetchone()[0],
            'blacklisted_tv': db.execute('SELECT COUNT(*) FROM tv_channels WHERE black_list = 1 AND status = 1').fetchone()[0],
            'duplicate_hashes': db.execute('''
                SELECT COUNT(*) FROM (
                    SELECT hash_midia, COUNT(*) as cnt
                    FROM midias
                    WHERE status = 1 AND black_list = 0
                    GROUP BY hash_midia
                    HAVING cnt > 1
                )
            ''').fetchone()[0],
            'duplicate_tv': db.execute('''
                SELECT COUNT(*) FROM (
                    SELECT hash_canal, COUNT(*) as cnt
                    FROM tv_channels
                    WHERE status = 1 AND black_list = 0
                    GROUP BY hash_canal
                    HAVING cnt > 1
                )
            ''').fetchone()[0],
        }

        return stats

    def clean_blacklist_from_gallery(self):
        """Remove arquivos .strm da galeria de itens marcados como blacklist."""
        from pathlib import Path
        from app.services.exporter import generate_file_path
        from app.services.config import get_galeria_path

        db = get_db()
        galeria_path = Path(get_galeria_path())

        # Get all blacklist items from database
        blacklist_items = db.execute('''
            SELECT id, hash_midia, nome_da_midia, categoria, url, ano, season, episode
            FROM midias 
            WHERE status = 1 AND black_list = 1
        ''').fetchall()

        deleted_count = 0
        error_count = 0

        for item in blacklist_items:
            try:
                # Generate the expected file path for this item
                media_dict = {
                    'hash_midia': item['hash_midia'],
                    'nome_da_midia': item['nome_da_midia'],
                    'categoria': item['categoria'],
                    'url': item['url'],
                    'ano': item['ano'],
                    'season': item['season'],
                    'episode': item['episode']
                }

                arquivo_path = Path(generate_file_path(media_dict))

                # Only delete .strm files (not tv.m3u or other files)
                if arquivo_path.exists() and arquivo_path.suffix == '.strm':
                    arquivo_path.unlink()
                    deleted_count += 1

                    # Try to remove empty parent directories
                    try:
                        arquivo_path.parent.rmdir()
                    except:
                        pass
            except Exception as e:
                error_count += 1

        # Also clean exported_media table for blacklist items
        db.execute('''
            DELETE FROM exported_media
            WHERE hash_midia IN (
                SELECT hash_midia FROM midias WHERE black_list = 1 AND status = 1
            )
        ''')
        db.commit()

        return {
            'deleted_files': deleted_count,
            'errors': error_count,
            'total_blacklist_items': len(blacklist_items)
        }

    def fix_duplicate_quality(self):
        """Detecta duplicatas e marca a pior qualidade como blacklist."""
        from app.services.parser import calculate_hash_midia, remove_quality_from_name
        import hashlib

        db = get_db()

        # Buscar todas as mídias não blacklisted
        media_items = db.execute('''
            SELECT id, nome_da_midia, nome_normalizado, categoria, ano
            FROM midias
            WHERE black_list = 0
        ''').fetchall()

        # Dicionário para agrupar por novo hash
        hash_groups = {}

        for item in media_items:
            media_id, nome_da_midia, nome_normalizado, categoria, ano = item

            # Recalcular hash com nova lógica (ignora ano)
            new_hash = calculate_hash_midia(categoria, nome_normalizado, ano)

            if new_hash not in hash_groups:
                hash_groups[new_hash] = []

            hash_groups[new_hash].append({
                'id': media_id,
                'nome_da_midia': nome_da_midia,
                'nome_normalizado': nome_normalizado,
                'categoria': categoria,
                'ano': ano,
                'hash': new_hash
            })

        # Encontrar duplicatas
        duplicates = {h: items for h, items in hash_groups.items() if len(items) > 1}

        blacklist_count = 0
        updated_hashes = []

        for hash_value, items in duplicates.items():
            # Ordenar por qualidade (melhor primeiro)
            items_sorted = sorted(items, key=lambda x: self._get_quality_score(x['nome_da_midia']), reverse=True)

            # Manter a primeira (melhor qualidade)
            best_item = items_sorted[0]

            # Atualizar hash do melhor item (apenas se for diferente)
            current_hash = db.execute('SELECT hash_midia FROM midias WHERE id = ?', (best_item['id'],)).fetchone()[0]
            if current_hash != hash_value:
                try:
                    db.execute('UPDATE midias SET hash_midia = ? WHERE id = ?', (hash_value, best_item['id']))
                    updated_hashes.append(best_item['id'])
                except Exception:
                    pass  # Se o hash já existe, não atualiza

            # Marcar os outros como blacklist
            for item in items_sorted[1:]:
                db.execute('UPDATE midias SET black_list = 1 WHERE id = ?', (item['id'],))
                blacklist_count += 1

        # Atualizar hashes dos itens únicos também
        for hash_value, items in hash_groups.items():
            if len(items) == 1:
                item = items[0]
                current_hash = db.execute('SELECT hash_midia FROM midias WHERE id = ?', (item['id'],)).fetchone()[0]
                if current_hash != hash_value:
                    try:
                        db.execute('UPDATE midias SET hash_midia = ? WHERE id = ?', (hash_value, item['id']))
                        updated_hashes.append(item['id'])
                    except Exception:
                        pass

        db.commit()

        return {
            'total_media': len(media_items),
            'duplicate_groups': len(duplicates),
            'blacklisted': blacklist_count,
            'hashes_updated': len(updated_hashes)
        }

    def clean_exact_duplicates(self):
        """Remove duplicatas de nomes idênticos, mantendo apenas uma cópia."""
        db = get_db()

        # Buscar todos os nomes que aparecem mais de uma vez
        duplicate_names = db.execute('''
            SELECT nome_da_midia, COUNT(*) as count
            FROM midias
            GROUP BY nome_da_midia
            HAVING count > 1
            ORDER BY count DESC
        ''').fetchall()

        total_removed = 0

        for nome, count in duplicate_names:
            # Buscar todos os registros com esse nome
            items = db.execute('''
                SELECT id, nome_da_midia, black_list, url, categoria
                FROM midias
                WHERE nome_da_midia = ?
                ORDER BY black_list ASC, id ASC
            ''', (nome,)).fetchall()

            if len(items) <= 1:
                continue

            # Manter o primeiro (prioridade: não blacklist, depois menor ID)
            keep_item = items[0]
            remove_items = items[1:]

            for item in remove_items:
                # Remover o duplicado
                db.execute('DELETE FROM midias WHERE id = ?', (item[0],))
                total_removed += 1

        db.commit()

        return {
            'duplicate_names': len(duplicate_names),
            'records_removed': total_removed
        }

    def _get_quality_score(self, nome):
        """Retorna pontuação de qualidade (maior = melhor)."""
        nome_lower = nome.lower()

        quality_scores = {
            'sd': 1,
            'dvdrip': 2,
            'hdtv': 3,
            'sdtv': 4,
            'web-dl': 5,
            'webdl': 5,
            'dvd': 6,
            'bdrip': 7,
            'brrip': 8,
            'bluray': 9,
            'hd': 10,
            'fhd': 11,
            '4k': 12,
            'hdr': 13,
        }

        max_score = 0
        for quality, score in quality_scores.items():
            if quality in nome_lower:
                max_score = max(max_score, score)

        if max_score == 0:
            max_score = 5

        # Penalidade por ter [L] (pior qualidade)
        if '[l]' in nome_lower:
            max_score = 0

        # Penalidade por ter ano no nome (considerado pior qualidade)
        if re.search(r'[\(\[]\d{4}[\)\]]', nome):
            max_score = max_score - 2

        return max_score

    def blacklist_duplicates_keep_lowest_quality(self):
        """Identifica duplicatas por nome sem qualidade/ano e marca as de maior qualidade como blacklist.
        
        Mantém a MENOR qualidade (prioridade: [L] > SD > HD > FHD > 4K > HDR).
        """
        from app.services.parser import remove_quality_from_name
        
        db = get_db()
        
        # Buscar todas as mídias ativas
        media_items = db.execute('''
            SELECT id, nome_da_midia, nome_normalizado, qualidade, black_list
            FROM midias
            WHERE status = 1 AND black_list = 0
        ''').fetchall()
        
        # Mapeamento de qualidade para score (menor = pior qualidade = mantém)
        # Inverso do normal: [L] é a pior (score 0), SD é melhor que [L], etc.
        quality_priority = {
            '[l]': 0,      # Pior qualidade - mantém
            'sd': 1,       # DVD/SD
            'dvdrip': 2,
            'hdtv': 3,
            'sdtv': 4,
            'web-dl': 5,
            'webdl': 5,
            'dvd': 6,
            'bdrip': 7,
            'brrip': 8,
            'bluray': 9,
            'hd': 10,
            'fhd': 11,
            '4k': 12,
            'hdr': 13,     # Melhor qualidade - remove
        }
        
        def get_lowest_quality_score(nome, qualidade):
            """Retorna score de qualidade (menor = pior = mantém)."""
            nome_lower = nome.lower()
            qualidade_lower = (qualidade or '').lower()
            
            min_score = 100  # Valor alto padrão
            
            # Verificar [L] primeiro
            if '[l]' in nome_lower or '[l]' in qualidade_lower:
                return 0
            
            # Verificar qualidades no nome e campo qualidade
            for q, score in quality_priority.items():
                if q in nome_lower or q in qualidade_lower:
                    min_score = min(min_score, score)
            
            # Se não encontrou qualidade, usa score médio
            if min_score == 100:
                min_score = 5
            
            return min_score
        
        # Agrupar por nome sem qualidade/ano
        from app.services.parser import remove_quality_from_name
        import re
        
        def get_base_name(nome):
            """Remove qualidade e ano do nome para comparação."""
            base = remove_quality_from_name(nome)
            # Remover ano entre parenteses ou colchetes
            base = re.sub(r'[\(\[\{]?\d{4}[\)\]\}]?', '', base)
            base = re.sub(r'\s+', ' ', base).strip()
            return base.lower()
        
        groups = {}
        for media in media_items:
            base_name = get_base_name(media['nome_da_midia'])
            if base_name not in groups:
                groups[base_name] = []
            groups[base_name].append({
                'id': media['id'],
                'nome': media['nome_da_midia'],
                'qualidade': media['qualidade'],
                'score': get_lowest_quality_score(media['nome_da_midia'], media['qualidade'])
            })
        
        # Processar grupos com duplicatas
        total_blacklisted = 0
        total_groups_processed = 0
        
        for base_name, group in groups.items():
            if len(group) > 1:
                # Ordenar por score (menor primeiro = pior qualidade primeiro)
                group.sort(key=lambda x: x['score'])
                
                # Manter o primeiro (pior qualidade)
                keep_item = group[0]
                blacklist_items = group[1:]
                
                # Marcar outros como blacklist
                for item in blacklist_items:
                    db.execute('UPDATE midias SET black_list = 1 WHERE id = ?', (item['id'],))
                    total_blacklisted += 1
                
                total_groups_processed += 1
        
        db.commit()
        
        return {
            'total_groups_processed': total_groups_processed,
            'total_blacklisted': total_blacklisted,
            'message': f'Processados {total_groups_processed} grupos de duplicatas. {total_blacklisted} itens marcados como blacklist.'
        }
