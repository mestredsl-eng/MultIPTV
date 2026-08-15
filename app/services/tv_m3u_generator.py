"""Service for generating TV M3U playlist compatible with Jellyfin."""

import logging
import sys
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET
import html

logger = logging.getLogger('process')


def _indent_xml(elem, level=0):
    """Add proper indentation to XML tree (Python 3.8+ compatible).
    
    FIXED: ET.indent() is only available in Python 3.9+
    This helper function provides compatibility with Python 3.8
    """
    indent_str = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent_str + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = indent_str
        for i, child in enumerate(elem):
            _indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent_str
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = indent_str


def generate_tv_m3u(db, output_path: Path, epg_path: Path = None) -> dict:
    """
    Generate TV M3U playlist from database TV channels.

    Args:
        db: Database connection
        output_path: Path to save the M3U file
        epg_path: Optional path to EPG file

    Returns:
        dict: Statistics about the generation
    """
    try:
        # Get all active TV channels from database
        channels = db.execute('''
            SELECT id, nome_canal, url, logo_url, categoria, tvg_id
            FROM tv_channels
            WHERE status = 1 AND black_list = 0
            ORDER BY nome_canal
        ''').fetchall()

        total_channels = len(channels)
        if total_channels == 0:
            logger.warning("Nenhum canal TV encontrado no banco")
            return {
                'success': False,
                'total_channels': 0,
                'error': 'Nenhum canal TV encontrado'
            }

        logger.info(f"Gerando tv.m3u com {total_channels} canais")

        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate M3U file
        with open(output_path, 'w', encoding='utf-8') as f:
            # M3U header
            f.write('#EXTM3U\n')
            f.write('#EXTINF:0,Mestre IPTV TV Channels\n\n')

            for channel in channels:
                channel_id = channel['id']
                channel_name = channel['nome_canal']
                url = channel['url']
                logo_url = channel['logo_url'] if 'logo_url' in channel.keys() else ''
                categoria = channel['categoria'] if 'categoria' in channel.keys() else ''
                tvg_id = channel['tvg_id'] if 'tvg_id' in channel.keys() else ''

                # Format channel entry for Jellyfin compatibility
                # Jellyfin prefers format: #EXTINF:-1 tvg-id="ID" tvg-logo="URL" tvg-name="NAME",Channel Name
                
                # Normalize tvg_id to match XML encoding (escape & as &amp;)
                # This ensures M3U tvg-id matches EPG channel id exactly
                if tvg_id:
                    tvg_id_normalized = html.escape(tvg_id)
                else:
                    # Use channel name as fallback
                    tvg_id_normalized = html.escape(channel_name)

                extinf_line = '#EXTINF:-1'

                # Add tvg-id with XML encoding
                extinf_line += f' tvg-id="{tvg_id_normalized}"'

                # Add logo if available
                if logo_url:
                    extinf_line += f' tvg-logo="{logo_url}"'

                # Add tvg-name for Jellyfin (also encode for consistency)
                extinf_line += f' tvg-name="{html.escape(channel_name)}"'

                # Add channel name at the end
                extinf_line += f',{channel_name}'

                f.write(extinf_line + '\n')
                f.write(url + '\n\n')

        logger.info(f"tv.m3u gerado com sucesso: {total_channels} canais")

        return {
            'success': True,
            'total_channels': total_channels,
            'output_path': str(output_path)
        }

    except Exception as e:
        logger.error(f"Erro ao gerar tv.m3u: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def generate_epg_xmltv(db, output_path: Path, epg_sources: list = None) -> dict:
    """
    Generate EPG XMLTV file from database TV channels and IPTV sources.

    Args:
        db: Database connection
        output_path: Path to save the EPG XML file
        epg_sources: List of EPG source URLs from IPTV sources

    Returns:
        dict: Statistics about the generation
    """
    try:
        from app.services.epg_fetcher import fetch_epg_from_url, parse_xmltv

        # Get all active TV channels from database
        channels = db.execute('''
            SELECT id, nome_canal, tvg_id, url
            FROM tv_channels
            WHERE status = 1 AND black_list = 0
            ORDER BY nome_canal
        ''').fetchall()

        total_channels = len(channels)
        if total_channels == 0:
            logger.warning("Nenhum canal TV encontrado para EPG")
            return {
                'success': False,
                'total_channels': 0,
                'error': 'Nenhum canal TV encontrado'
            }

        logger.info(f"Gerando EPG XMLTV para {total_channels} canais")

        # Create XMLTV root element
        root = ET.Element('tv')
        root.set('generator-info-name', 'Mestre IPTV Manager')
        root.set('generator-info-url', 'https://github.com')

        # Map to store program data for each channel
        channel_programs = {}

        # Get IPTV sources with EPG URLs
        if epg_sources:
            logger.info(f"Baixando EPG de {len(epg_sources)} fontes")

            cache_dir = Path(__file__).parent.parent.parent / 'cache' / 'epg'
            cache_dir.mkdir(parents=True, exist_ok=True)

            # Download and merge EPG from sources
            for epg_url in epg_sources:
                try:
                    xml_content = fetch_epg_from_url(epg_url, cache_dir, use_cache=True)
                    if xml_content:
                        parsed_channels = parse_xmltv(xml_content)

                        # Map external channels to our database channels
                        for ext_channel_id, channel_data in parsed_channels.items():
                            channel_name = channel_data['name']
                            
                            # Find matching channel in our database
                            matched_channel = None
                            for db_channel in channels:
                                if channel_name.lower() in db_channel['nome_canal'].lower():
                                    matched_channel = db_channel
                                    break
                            
                            if matched_channel:
                                # Use our tvg_id instead of external channel id
                                our_channel_id = matched_channel['tvg_id'] if matched_channel['tvg_id'] else str(matched_channel['id'])
                                
                                if our_channel_id not in channel_programs:
                                    channel_programs[our_channel_id] = {
                                        'name': matched_channel['nome_canal'],
                                        'programs': channel_data['programs']
                                    }
                                else:
                                    # Merge programs
                                    channel_programs[our_channel_id]['programs'].extend(channel_data['programs'])

                except Exception as e:
                    logger.warning(f"Erro ao processar EPG de {epg_url}: {e}")

        # Add all our TV channels to the EPG
        for channel in channels:
            channel_id = channel['tvg_id'] if 'tvg_id' in channel.keys() else str(channel['id'])
            channel_name = channel['nome_canal']

            # Add channel element
            channel_elem = ET.SubElement(root, 'channel')
            channel_elem.set('id', channel_id)

            display_name = ET.SubElement(channel_elem, 'display-name')
            display_name.text = channel_name

            # Add programs if available for this channel
            if channel_id in channel_programs:
                for program in channel_programs[channel_id]['programs']:
                    prog_elem = ET.SubElement(root, 'programme')
                    prog_elem.set('channel', channel_id)
                    prog_elem.set('start', program['start'])
                    prog_elem.set('stop', program['stop'])

                    title = ET.SubElement(prog_elem, 'title')
                    title.text = program['title']

                    if program.get('desc'):
                        desc = ET.SubElement(prog_elem, 'desc')
                        desc.text = program['desc']

        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write XML file with proper formatting
        tree = ET.ElementTree(root)
        
        # Add proper indentation (compatible with Python 3.8+)
        if sys.version_info >= (3, 9):
            # Use native ET.indent if available
            ET.indent(tree, space="  ", level=0)
        else:
            # Use custom indent function for Python 3.8
            _indent_xml(root, level=0)
        
        tree.write(output_path, encoding='utf-8', xml_declaration=True)

        logger.info(f"EPG XMLTV gerado com sucesso: {output_path}")

        return {
            'success': True,
            'total_channels': total_channels,
            'output_path': str(output_path)
        }

    except Exception as e:
        logger.error(f"Erro ao gerar EPG XMLTV: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def generate_jellyfin_package(db, output_dir: Path, epg_sources: list = None) -> dict:
    """
    Generate complete Jellyfin package: TV M3U and EPG XMLTV.

    Args:
        db: Database connection
        output_dir: Directory to save the files
        epg_sources: List of EPG source URLs from IPTV sources

    Returns:
        dict: Statistics about the generation
    """
    try:
        logger.info("Gerando pacote completo Jellyfin (tv.m3u + epg.xml)")

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate TV M3U
        m3u_path = output_dir / 'tv.m3u'
        m3u_result = generate_tv_m3u(db, m3u_path)

        if not m3u_result['success']:
            return {
                'success': False,
                'error': f"Erro ao gerar tv.m3u: {m3u_result['error']}"
            }

        # Generate EPG XMLTV
        epg_path = output_dir / 'epg.xml'
        epg_result = generate_epg_xmltv(db, epg_path, epg_sources)

        if not epg_result['success']:
            logger.warning(f"Erro ao gerar EPG (continuando): {epg_result['error']}")

        logger.info("Pacote Jellyfin gerado com sucesso")

        return {
            'success': True,
            'm3u_path': str(m3u_path),
            'epg_path': str(epg_path),
            'total_channels': m3u_result['total_channels'],
            'm3u_success': m3u_result['success'],
            'epg_success': epg_result['success']
        }

    except Exception as e:
        logger.error(f"Erro ao gerar pacote Jellyfin: {e}")
        return {
            'success': False,
            'error': str(e)
        }
