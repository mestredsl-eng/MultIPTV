"""EPG (Electronic Program Guide) service for IPTV."""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path


def download_epg(url_epg):
    """Download EPG XML from URL."""
    try:
        response = requests.get(url_epg, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error downloading EPG: {e}")
        return None


def parse_epg(epg_xml):
    """Parse EPG XML and extract channel and program data."""
    try:
        root = ET.fromstring(epg_xml)
        
        channels = {}
        programs = []
        
        # Parse channels
        for channel in root.findall('channel'):
            channel_id = channel.get('id')
            channel_name = channel.find('display-name')
            if channel_name is not None:
                channels[channel_id] = channel_name.text
        
        # Parse programs
        for programme in root.findall('programme'):
            channel_id = programme.get('channel')
            start = programme.get('start')
            stop = programme.get('stop')
            
            title_elem = programme.find('title')
            desc_elem = programme.find('desc')
            
            if title_elem is not None:
                programs.append({
                    'channel_id': channel_id,
                    'start': start,
                    'stop': stop,
                    'title': title_elem.text,
                    'description': desc_elem.text if desc_elem is not None else ''
                })
        
        return channels, programs
    except Exception as e:
        print(f"Error parsing EPG: {e}")
        return {}, []


def save_epg(epg_xml, output_path):
    """Save EPG XML to file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(epg_xml)
        return True
    except Exception as e:
        print(f"Error saving EPG: {e}")
        return False


def generate_epg_from_iptv(iptv_sources, output_path):
    """Generate EPG from IPTV sources."""
    root = ET.Element('tv')
    root.set('generator-info-name', 'Mestre IPTV Manager')
    root.set('generator-info-url', 'https://github.com')
    
    channel_id = 1
    
    for iptv in iptv_sources:
        if iptv.get('url_epg'):
            # Download EPG from IPTV source
            epg_xml = download_epg(iptv['url_epg'])
            if epg_xml:
                # Parse and merge EPG
                channels, programs = parse_epg(epg_xml)
                
                # Add channels to root
                for ch_id, ch_name in channels.items():
                    channel_elem = ET.SubElement(root, 'channel')
                    channel_elem.set('id', ch_id)
                    display_name = ET.SubElement(channel_elem, 'display-name')
                    display_name.text = ch_name
                
                # Add programs to root
                for prog in programs:
                    prog_elem = ET.SubElement(root, 'programme')
                    prog_elem.set('channel', prog['channel_id'])
                    prog_elem.set('start', prog['start'])
                    prog_elem.set('stop', prog['stop'])
                    
                    title = ET.SubElement(prog_elem, 'title')
                    title.text = prog['title']
                    
                    if prog['description']:
                        desc = ET.SubElement(prog_elem, 'desc')
                        desc.text = prog['description']
    
    # Write to file
    tree = ET.ElementTree(root)
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    
    return True
