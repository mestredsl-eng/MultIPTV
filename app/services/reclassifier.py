"""Intelligent reclassification service for media items."""

import json
import re
from typing import Dict, List, Tuple


class MediaReclassifier:
    """Intelligent media reclassifier with scoring system."""
    
    def __init__(self):
        self.categories = ['TV', 'Movie', 'Series', 'Novela', 'Cartoon', 'Documentary', 'Sports', 'Educational', 'Adult', 'Unknown']
        self.rules = self._build_rules()
    
    def _build_rules(self) -> Dict[str, List[Dict]]:
        """Build scoring rules for each category based on data analysis."""
        return {
            'TV': [
                # Channel indicators
                {'pattern': r'\b(Canal|Channel|TV|Televisão)\b', 'score': 30, 'reason': 'channel_keyword'},
                {'pattern': r'\b(Globo|SBT|Record|Band|RedeTV|Cultura)\b', 'score': 40, 'reason': 'brazilian_network'},
                {'pattern': r'\b(HBO|CNN|Discovery|History|NatGeo|ESPN|Fox|MTV)\b', 'score': 35, 'reason': 'international_channel'},
                {'pattern': r'\b(4K|FHD|HD|SD)\s*$', 'score': 15, 'reason': 'quality_suffix'},
                {'pattern': r'\.ts$', 'score': 25, 'reason': 'stream_extension'},
                # No season/episode
                {'pattern': r'^(?!.*S\d{1,2}E\d{1,2})(?!.*Season)(?!.*Episode)', 'score': 20, 'reason': 'no_season_episode'},
            ],
            'Movie': [
                # Quality indicators
                {'pattern': r'\b(1080p|720p|480p|BluRay|WEB-DL|WEBRip|BRRip|DVDRip)\b', 'score': 30, 'reason': 'quality_indicator'},
                {'pattern': r'\b(Movie|Filme|Cinema)\b', 'score': 25, 'reason': 'movie_keyword'},
                {'pattern': r'\.mp4$', 'score': 20, 'reason': 'movie_extension'},
                {'pattern': r'/movie/', 'score': 25, 'reason': 'movie_path'},
                # Year pattern
                {'pattern': r'\b(19|20)\d{2}\b', 'score': 15, 'reason': 'year_present'},
            ],
            'Series': [
                # Season/Episode indicators
                {'pattern': r'\bS\d{1,2}E\d{1,2}\b', 'score': 50, 'reason': 'season_episode_format'},
                {'pattern': r'\bSeason\s*\d+\b', 'score': 40, 'reason': 'season_keyword'},
                {'pattern': r'\bEpisode\s*\d+\b', 'score': 40, 'reason': 'episode_keyword'},
                {'pattern': r'\b(Temporada|Temp\.|Episódio|Ep\.|Ep)\b', 'score': 35, 'reason': 'portuguese_season_episode'},
                {'pattern': r'\bS\d{1,2}\b(?!E)', 'score': 30, 'reason': 'season_only'},
            ],
            'Novela': [
                {'pattern': r'\b(Novela|Telenovela|Soap Opera)\b', 'score': 50, 'reason': 'novela_keyword'},
                {'pattern': r'\b(Globo Novelas|SBT Novelas|Record Novelas)\b', 'score': 45, 'reason': 'novela_package'},
                {'pattern': r'\b(9pm|7pm|6pm)\s*Novelas\b', 'score': 40, 'reason': 'novela_timeslot'},
                # Brazilian soap opera titles
                {'pattern': r'\b(América|O Rei do Gado|Terra Nostra|Caminho das Índias|Cobras & Lagartos)\b', 'score': 35, 'reason': 'brazilian_soap'},
            ],
            'Cartoon': [
                {'pattern': r'\b(Cartoon|Animation|Anime|Desenho|Animação)\b', 'score': 40, 'reason': 'cartoon_keyword'},
                {'pattern': r'\b(Cartoon Network|Disney|Nickelodeon|Boomerang)\b', 'score': 45, 'reason': 'cartoon_channel'},
                {'pattern': r'\b(SpongeBob|Tom & Jerry|Scooby-Doo|Pokémon|Dragon Ball)\b', 'score': 35, 'reason': 'cartoon_character'},
            ],
            'Documentary': [
                {'pattern': r'\b(Discovery|National Geographic|History Channel|Animal Planet)\b', 'score': 50, 'reason': 'documentary_channel'},
                {'pattern': r'\b(Documentary|Documentário|Doc)\b', 'score': 40, 'reason': 'documentary_keyword'},
                {'pattern': r'\b(Nature|Science|History|Wildlife|Space)\b', 'score': 30, 'reason': 'documentary_topic'},
            ],
            'Sports': [
                {'pattern': r'\b(ESPN|SportTV|Premiere|Combate|Fox Sports|SporTV)\b', 'score': 50, 'reason': 'sports_channel'},
                {'pattern': r'\b(Futebol|Soccer|Football|Basquete|Basketball|Tênis|Tennis)\b', 'score': 40, 'reason': 'sports_keyword'},
                {'pattern': r'\b(NBA|NFL|MLB|NHL|F1|Formula 1|UFC|MMA)\b', 'score': 45, 'reason': 'sports_league'},
                {'pattern': r'\b(Copa|World Cup|Champions League|Libertadores)\b', 'score': 45, 'reason': 'sports_tournament'},
            ],
            'Educational': [
                {'pattern': r'\b(Educational|Educação|Learning|Curso|Aula)\b', 'score': 40, 'reason': 'educational_keyword'},
                {'pattern': r'\b(TED|TEDx|Khan Academy|Coursera)\b', 'score': 35, 'reason': 'educational_platform'},
                {'pattern': r'\b(Documentary|Documentário)\b', 'score': 25, 'reason': 'educational_documentary'},
            ],
            'Adult': [
                {'pattern': r'\b(XXX|Adult|Porn|Erotic)\b', 'score': 50, 'reason': 'adult_keyword'},
                {'pattern': r'\b(Brazzers|Reality Kings|Bangbros|Naughty America)\b', 'score': 45, 'reason': 'adult_studio'},
                {'pattern': r'\b(Hustler|Penthouse|Playboy)\b', 'score': 40, 'reason': 'adult_brand'},
            ],
            'Unknown': [
                # Default category when no rules match
            ]
        }
    
    def _calculate_score(self, media_item: Dict) -> Dict[str, Tuple[float, List[str]]]:
        """Calculate score for each category based on media item data."""
        scores = {cat: (0.0, []) for cat in self.categories}
        
        # Get relevant fields
        nome = media_item.get('nome_da_midia', '')
        nome_normalizado = media_item.get('nome_normalizado', '')
        url = media_item.get('url', '')
        season = media_item.get('season')
        episode = media_item.get('episode')
        
        # Combine all text for analysis
        text_to_analyze = f"{nome} {nome_normalizado} {url}".lower()
        
        # Calculate scores for each category
        for category, rules in self.rules.items():
            total_score = 0.0
            reasons = []
            
            for rule in rules:
                pattern = rule['pattern']
                score = rule['score']
                reason = rule['reason']
                
                try:
                    if re.search(pattern, text_to_analyze, re.IGNORECASE):
                        total_score += score
                        reasons.append(f"+{score} {reason}")
                except re.error:
                    # Skip invalid patterns
                    pass
            
            # Special handling for season/episode
            if season and episode:
                if category == 'Series':
                    total_score += 50
                    reasons.append(f"+50 season_episode_present")
                elif category == 'TV':
                    total_score -= 30  # Penalize TV if has season/episode
                    reasons.append(f"-30 has_season_episode")
            
            scores[category] = (total_score, reasons)
        
        return scores
    
    def _determine_category(self, scores: Dict[str, Tuple[float, List[str]]]) -> Tuple[str, float, List[str]]:
        """Determine the best category based on scores."""
        # Find category with highest score
        best_category = 'Unknown'
        best_score = 0.0
        best_reasons = []
        
        for category, (score, reasons) in scores.items():
            if score > best_score:
                best_score = score
                best_category = category
                best_reasons = reasons
        
        # Calculate confidence (score / max possible score)
        max_possible_score = sum(rule['score'] for rules in self.rules.values() for rule in rules)
        confidence = min(best_score / max_possible_score * 100, 100.0) if max_possible_score > 0 else 0.0
        
        return best_category, confidence, best_reasons
    
    def reclassify_media(self, media_item: Dict) -> Dict:
        """Reclassify a single media item."""
        current_category = media_item.get('categoria', 'Unknown')
        
        # Calculate scores
        scores = self._calculate_score(media_item)
        
        # Determine best category
        new_category, confidence, reasons = self._determine_category(scores)
        
        # Build score JSON
        score_json = {cat: score for cat, (score, _) in scores.items()}
        
        # Build reason string
        reason_str = " | ".join(reasons) if reasons else "no_rules_matched"
        
        return {
            'media_id': media_item['id'],
            'current_category': current_category,
            'new_category': new_category,
            'confidence': confidence,
            'score_json': score_json,
            'reason': reason_str,
            'changed': current_category != new_category
        }
    
    def reclassify_batch(self, media_items: List[Dict]) -> List[Dict]:
        """Reclassify a batch of media items."""
        return [self.reclassify_media(item) for item in media_items]
