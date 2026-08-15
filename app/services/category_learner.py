"""Category learning service - learns from user manual category corrections."""

from typing import Optional, Dict, List
from app.database import get_db
from app.services.parser import normalize_name


class CategoryLearner:
    """Service that learns from user manual category corrections and applies them to similar media."""
    
    def __init__(self):
        self.db = get_db()
    
    def record_correction(self, media_id: int, old_category: str, new_category: str) -> bool:
        """Record a manual category correction made by the user.
        
        Args:
            media_id: ID of the media item that was corrected
            old_category: The category before correction
            new_category: The category after correction
            
        Returns:
            True if correction was recorded successfully
        """
        # Get media details
        media = self.db.execute(
            'SELECT hash_midia, nome_normalizado FROM midias WHERE id = ?',
            (media_id,)
        ).fetchone()
        
        if not media:
            return False
        
        hash_midia = media['hash_midia']
        nome_normalizado = media['nome_normalizado']
        
        # Check if correction already exists
        existing = self.db.execute(
            'SELECT id FROM category_corrections WHERE hash_midia = ? AND nome_normalizado = ?',
            (hash_midia, nome_normalizado)
        ).fetchone()
        
        if existing:
            # Update existing correction
            self.db.execute('''
                UPDATE category_corrections 
                SET categoria_anterior = ?, categoria_nova = ?, data_correcao = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (old_category, new_category, existing['id']))
        else:
            # Insert new correction
            self.db.execute('''
                INSERT INTO category_corrections (hash_midia, nome_normalizado, categoria_anterior, categoria_nova)
                VALUES (?, ?, ?, ?)
            ''', (hash_midia, nome_normalizado, old_category, new_category))
        
        self.db.commit()
        return True
    
    def get_learned_category(self, hash_midia: str, nome_normalizado: str) -> Optional[str]:
        """Get learned category for a media item based on hash or normalized name.
        
        Priority:
        1. Exact hash match (highest priority - same media)
        2. Exact normalized name match (same title)
        3. Partial name match (similar titles)
        
        Args:
            hash_midia: Hash of the media item
            nome_normalizado: Normalized name of the media item
            
        Returns:
            Learned category if found, None otherwise
        """
        # Priority 1: Exact hash match
        correction = self.db.execute(
            'SELECT categoria_nova FROM category_corrections WHERE hash_midia = ?',
            (hash_midia,)
        ).fetchone()
        
        if correction:
            self._increment_application_count(hash_midia, nome_normalizado)
            return correction['categoria_nova']
        
        # Priority 2: Exact normalized name match
        correction = self.db.execute(
            'SELECT categoria_nova FROM category_corrections WHERE nome_normalizado = ?',
            (nome_normalizado,)
        ).fetchone()
        
        if correction:
            self._increment_application_count(hash_midia, nome_normalizado)
            return correction['categoria_nova']
        
        # Priority 3: Partial name match (fuzzy matching)
        # Try to find corrections with similar names
        corrections = self.db.execute(
            'SELECT categoria_nova, COUNT(*) as count FROM category_corrections '
            'WHERE nome_normalizado LIKE ? '
            'GROUP BY categoria_nova '
            'ORDER BY count DESC LIMIT 1',
            (f'%{nome_normalizado[:20]}%',)  # Match first 20 chars
        ).fetchall()
        
        if corrections and corrections[0]['count'] >= 2:  # Need at least 2 similar matches
            category = corrections[0]['categoria_nova']
            self._increment_application_count(hash_midia, nome_normalizado)
            return category
        
        return None
    
    def _increment_application_count(self, hash_midia: str, nome_normalizado: str):
        """Increment the application count for a correction."""
        self.db.execute('''
            UPDATE category_corrections 
            SET vezes_aplicada = vezes_aplicada + 1, ultima_aplicacao = CURRENT_TIMESTAMP
            WHERE hash_midia = ? OR nome_normalizado = ?
        ''', (hash_midia, nome_normalizado))
        self.db.commit()
    
    def get_learning_stats(self) -> Dict:
        """Get statistics about the learning system.
        
        Returns:
            Dictionary with learning statistics
        """
        total_corrections = self.db.execute(
            'SELECT COUNT(*) as count FROM category_corrections'
        ).fetchone()['count']
        
        total_applications = self.db.execute(
            'SELECT SUM(vezes_aplicada) as total FROM category_corrections'
        ).fetchone()['total'] or 0
        
        most_common_corrections = self.db.execute('''
            SELECT categoria_nova, COUNT(*) as count 
            FROM category_corrections 
            GROUP BY categoria_nova 
            ORDER BY count DESC 
            LIMIT 5
        ''').fetchall()
        
        most_applied_corrections = self.db.execute('''
            SELECT categoria_nova, SUM(vezes_aplicada) as total 
            FROM category_corrections 
            GROUP BY categoria_nova 
            ORDER BY total DESC 
            LIMIT 5
        ''').fetchall()
        
        return {
            'total_corrections': total_corrections,
            'total_applications': total_applications,
            'most_common_corrections': [dict(row) for row in most_common_corrections],
            'most_applied_corrections': [dict(row) for row in most_applied_corrections]
        }
    
    def get_recent_corrections(self, limit: int = 20) -> List[Dict]:
        """Get recent category corrections.
        
        Args:
            limit: Maximum number of corrections to return
            
        Returns:
            List of recent corrections
        """
        corrections = self.db.execute('''
            SELECT * FROM category_corrections 
            ORDER BY data_correcao DESC 
            LIMIT ?
        ''', (limit,)).fetchall()
        
        return [dict(correction) for correction in corrections]
    
    def clear_old_corrections(self, days: int = 90) -> int:
        """Clear corrections older than specified days.
        
        Args:
            days: Number of days to keep corrections
            
        Returns:
            Number of corrections deleted
        """
        cursor = self.db.execute('''
            DELETE FROM category_corrections 
            WHERE data_correcao < datetime('now', '-' || ? || ' days')
        ''', (days,))
        
        deleted_count = cursor.rowcount
        self.db.commit()
        
        return deleted_count


# Convenience function for quick usage
def get_learned_category(hash_midia: str, nome_normalizado: str) -> Optional[str]:
    """Quick function to get learned category for a media item."""
    learner = CategoryLearner()
    return learner.get_learned_category(hash_midia, nome_normalizado)


def record_category_correction(media_id: int, old_category: str, new_category: str) -> bool:
    """Quick function to record a manual category correction."""
    learner = CategoryLearner()
    return learner.record_correction(media_id, old_category, new_category)
