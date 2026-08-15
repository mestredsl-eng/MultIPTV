"""Centralized duplicate management service for consistent blacklist checking across the system."""

import re
import logging
from app.services.parser import remove_quality_from_name

logger = logging.getLogger('process')


class DuplicateManager:
    """Centralized service for duplicate detection and blacklist checking."""
    
    def __init__(self, db):
        self.db = db
    
    def get_base_name(self, nome_normalizado):
        """
        Extract base name without quality indicators and year.
        Used for rigorous duplicate detection.
        """
        nome_base = remove_quality_from_name(nome_normalizado)
        nome_base = re.sub(r'\s*[\(\[]\d{4}[\)\]]\s*', '', nome_base)
        nome_base = re.sub(r'\s+', ' ', nome_base).strip().lower()
        return nome_base
    
    def check_rigorous_blacklist(self, nome_normalizado):
        """
        Check if a media should be skipped due to rigorous blacklist checking.
        Returns (should_skip: bool, reason: str, skip_count: int)
        
        Performance optimized: Cache-friendly query pattern.
        """
        nome_base = self.get_base_name(nome_normalizado)
        
        # Only check if base name is meaningful
        if not nome_base or len(nome_base) <= 3:
            return False, None, 0
        
        # OPTIMIZED: Single efficient query with LIMIT
        # This checks both exact and partial matches in one go
        duplicate_by_base = self.db.execute('''
            SELECT id, black_list, qualidade, nome_da_midia FROM midias 
            WHERE nome_normalizado LIKE ? AND status = 1 AND black_list = 1
            LIMIT 1
        ''', (f'%{nome_base}%',)).fetchone()
        
        if duplicate_by_base:
            reason = f"Blacklisted base name duplicate: {duplicate_by_base[3]}"
            return True, reason, 1
        
        return False, None, 0
    
    def find_duplicates_by_hash(self, hash_midia, exclude_id=None):
        """
        Find duplicates by hash_midia.
        Returns list of duplicate items.
        """
        if exclude_id:
            duplicates = self.db.execute('''
                SELECT * FROM midias
                WHERE hash_midia = ? AND id != ? AND status = 1
                ORDER BY nome_da_midia
            ''', (hash_midia, exclude_id)).fetchall()
        else:
            duplicates = self.db.execute('''
                SELECT * FROM midias
                WHERE hash_midia = ? AND status = 1
                ORDER BY nome_da_midia
            ''', (hash_midia,)).fetchall()
        
        return [dict(item) for item in duplicates]
    
    def find_duplicates_by_base_name(self, nome_normalizado, exclude_id=None):
        """
        Find duplicates by base name (without quality/year).
        Returns list of potential duplicate items.
        
        Performance optimized: Simple, efficient query with LIMIT.
        """
        nome_base = self.get_base_name(nome_normalizado)
        
        if not nome_base or len(nome_base) <= 3:
            return []
        
        # OPTIMIZED: Simple efficient query with LIMIT to avoid large result sets
        if exclude_id:
            duplicates = self.db.execute('''
                SELECT id, black_list, qualidade, nome_da_midia, nome_normalizado FROM midias 
                WHERE nome_normalizado LIKE ? AND id != ? AND status = 1
                LIMIT 50
            ''', (f'%{nome_base}%', exclude_id)).fetchall()
        else:
            duplicates = self.db.execute('''
                SELECT id, black_list, qualidade, nome_da_midia, nome_normalizado FROM midias 
                WHERE nome_normalizado LIKE ? AND status = 1
                LIMIT 50
            ''', (f'%{nome_base}%',)).fetchall()
        
        return [dict(item) for item in duplicates]
    
    def find_all_duplicates(self, media_id):
        """
        Find all duplicates of a media item by both hash and base name.
        Returns dict with 'hash_duplicates' and 'name_duplicates'.
        """
        # Get media info
        media = self.db.execute('''
            SELECT id, hash_midia, nome_normalizado FROM midias WHERE id = ?
        ''', (media_id,)).fetchone()
        
        if not media:
            return {'hash_duplicates': [], 'name_duplicates': [], 'error': 'Media not found'}
        
        # Find by hash
        hash_duplicates = self.find_duplicates_by_hash(media['hash_midia'], exclude_id=media_id)
        
        # Find by base name
        name_duplicates = self.find_duplicates_by_base_name(media['nome_normalizado'], exclude_id=media_id)
        
        # Remove exact duplicates (items that appear in both lists)
        hash_ids = {item['id'] for item in hash_duplicates}
        unique_name_duplicates = [item for item in name_duplicates if item['id'] not in hash_ids]
        
        return {
            'hash_duplicates': hash_duplicates,
            'name_duplicates': unique_name_duplicates,
            'total_duplicates': len(hash_duplicates) + len(unique_name_duplicates)
        }
    
    def process_duplicate_group(self, item_ids, keep_first=True):
        """
        Process a group of duplicate items.
        If keep_first=True, keeps the first item and blacklists the rest.
        Returns number of items blacklisted.
        """
        if len(item_ids) <= 1:
            return 0
        
        if keep_first:
            keep_id = item_ids[0]
            blacklist_ids = item_ids[1:]
        else:
            # If not keeping first, need quality-based logic
            # For now, simple implementation
            keep_id = item_ids[0]
            blacklist_ids = item_ids[1:]
        
        blacklist_count = 0
        for duplicate_id in blacklist_ids:
            self.db.execute('UPDATE midias SET black_list = 1 WHERE id = ?', (duplicate_id,))
            blacklist_count += 1
        
        self.db.commit()
        return blacklist_count
    
    def auto_propagate_blacklist(self, media_id):
        """
        Automatically propagate blacklist to all media with similar names.
        When a media is blacklisted, all media with similar base names should also be blacklisted.
        Returns count of newly blacklisted items.
        """
        # Get the media info
        media = self.db.execute('''
            SELECT id, nome_da_midia, nome_normalizado, black_list FROM midias WHERE id = ?
        ''', (media_id,)).fetchone()
        
        if not media:
            return 0
        
        # Only propagate if this media is being blacklisted
        if media['black_list'] != 1:
            return 0
        
        nome_base = self.get_base_name(media['nome_normalizado'] or media['nome_da_midia'])
        
        if not nome_base or len(nome_base) <= 3:
            return 0
        
        # Find all media with similar base names that are not yet blacklisted
        similar_media = self.db.execute('''
            SELECT id, nome_da_midia, nome_normalizado FROM midias 
            WHERE nome_normalizado LIKE ? AND status = 1 AND black_list = 0 AND id != ?
        ''', (f'%{nome_base}%', media_id)).fetchall()
        
        newly_blacklisted = 0
        for item in similar_media:
            self.db.execute('UPDATE midias SET black_list = 1 WHERE id = ?', (item['id'],))
            newly_blacklisted += 1
            logger.info(f"Auto-blacklisted media {item['id']}: {item['nome_da_midia']} (similar to blacklisted: {media['nome_da_midia']})")
        
        if newly_blacklisted > 0:
            self.db.commit()
            logger.info(f"Auto-propagated blacklist for '{media['nome_da_midia']}' to {newly_blacklisted} similar items")
        
        return newly_blacklisted
    
    def check_and_apply_auto_blacklist(self, nome_normalizado, nome_da_midia):
        """
        Check if a media name should be auto-blacklisted based on existing blacklisted items.
        If any blacklisted item has a similar name, automatically blacklist this new media.
        Returns (should_blacklist: bool, reason: str)
        """
        nome_base = self.get_base_name(nome_normalizado)
        
        if not nome_base or len(nome_base) <= 3:
            return False, None
        
        # Check if there are blacklisted items with similar base names
        blacklisted_similar = self.db.execute('''
            SELECT nome_da_midia FROM midias 
            WHERE nome_normalizado LIKE ? AND status = 1 AND black_list = 1
            LIMIT 1
        ''', (f'%{nome_base}%',)).fetchone()
        
        if blacklisted_similar:
            reason = f"Auto-blacklisted due to similarity with banned item: {blacklisted_similar['nome_da_midia']}"
            logger.info(f"Auto-blacklisting '{nome_da_midia}' - {reason}")
            return True, reason
        
        return False, None
    
    def apply_auto_blacklist_to_all_existing(self):
        """
        Apply auto-blacklist to all existing non-blacklisted media.
        Checks all media that are not blacklisted and blacklists them if they have names similar to banned items.
        Returns count of newly blacklisted items.
        """
        # Get all non-blacklisted media
        non_blacklisted = self.db.execute('''
            SELECT id, nome_da_midia, nome_normalizado FROM midias 
            WHERE black_list = 0 AND status = 1
        ''').fetchall()
        
        total_newly_blacklisted = 0
        
        for item in non_blacklisted:
            should_blacklist, reason = self.check_and_apply_auto_blacklist(
                item['nome_normalizado'], item['nome_da_midia']
            )
            
            if should_blacklist:
                self.db.execute('UPDATE midias SET black_list = 1 WHERE id = ?', (item['id'],))
                total_newly_blacklisted += 1
                logger.info(f"Auto-blacklisted existing media {item['id']}: {item['nome_da_midia']} - {reason}")
        
        if total_newly_blacklisted > 0:
            self.db.commit()
            logger.info(f"Auto-blacklisted {total_newly_blacklisted} existing media items based on similar banned names")
        
        return total_newly_blacklisted
    
    def get_statistics(self):
        """
        Get statistics about duplicates in the system.
        """
        stats = {
            'total_media': self.db.execute('SELECT COUNT(*) FROM midias WHERE status = 1').fetchone()[0],
            'blacklisted_media': self.db.execute('SELECT COUNT(*) FROM midias WHERE black_list = 1 AND status = 1').fetchone()[0],
        }
        
        return stats