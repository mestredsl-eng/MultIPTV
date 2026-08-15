"""Script to update classification process to use DuplicateManager."""

with open('app/routes/api.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_code = """                    else:
                        total_skipped += 1
                    continue
                # RIGOROUS DUPLICATE CHECK: Check for duplicates by normalized name without quality/year
                # Get base name (without quality/year) for aggressive duplicate detection
                nome_base = remove_quality_from_name(nome_normalizado)
                nome_base = re.sub(r'\s*[\(\[]\d{4}[\)\]]\s*', '', nome_base)
                nome_base = re.sub(r'\s+', ' ', nome_base).strip().lower()
                
                # Check if any media with same base name exists (aggressive duplicate detection)
                if nome_base and len(nome_base) > 3:  # Only check if base name is meaningful
                    duplicate_by_base = db.execute('''
                        SELECT id, black_list, qualidade, nome_da_midia FROM midias 
                        WHERE nome_normalizado LIKE ? AND status = 1
                    ''', (f'%{nome_base}%',)).fetchall()
                    
                    if duplicate_by_base:
                        # Found potential duplicates by base name
                        # Check if any of them are blacklisted
                        blacklisted_duplicates = [d for d in duplicate_by_base if d[1] == 1]
                        
                        if blacklisted_duplicates:
                            # RIGOROUS: If duplicates exist and are blacklisted, skip this one too
                            total_skipped += 1
                            total_skipped_rigorous += 1
                            logger.info(f"SKIP (RIGOROUS): '{entry['name']}' skipped due to blacklisted base name duplicate: {blacklisted_duplicates[0][3]}")
                            continue


                # Insert into database"""

new_code = """                    else:
                        total_skipped += 1
                    continue

                # RIGOROUS DUPLICATE CHECK using centralized DuplicateManager
                from app.services.duplicate_manager import DuplicateManager
                duplicate_manager = DuplicateManager(db)
                
                should_skip, skip_reason, skip_count = duplicate_manager.check_rigorous_blacklist(nome_normalizado)
                
                if should_skip:
                    total_skipped += 1
                    total_skipped_rigorous += 1
                    logger.info(f"SKIP (RIGOROUS): '{entry['name']}' skipped - {skip_reason}")
                    continue

                # Insert into database"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open('app/routes/api.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✅ Código atualizado para usar DuplicateManager')
else:
    print('❌ Código antigo não encontrado')
    print('Procurando por parte do código...')
    if '# RIGOROUS DUPLICATE CHECK' in content:
        print('✅ Encontrado marcador de verificação rigorosa')
    else:
        print('❌ Marcador não encontrado')
