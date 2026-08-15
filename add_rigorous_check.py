"""Script para adicionar verificação rigorosa de duplicatas no processo de classificação."""

# Ler o arquivo original
with open('app/routes/api.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Encontrar o ponto onde inserir a verificação rigorosa
insert_point = None
for i, line in enumerate(lines):
    if '                    else:' in line:
        if i + 1 < len(lines) and '                        total_skipped += 1' in lines[i + 1]:
            if i + 2 < len(lines) and '                    continue' in lines[i + 2]:
                if i + 3 < len(lines) and lines[i + 3].strip() == '':
                    if i + 4 < len(lines) and '# Insert into database' in lines[i + 4]:
                        insert_point = i + 3
                        break

if insert_point is None:
    print("❌ Não foi possível encontrar o ponto de inserção")
    exit(1)

# Código para inserir
rigorous_check = """                # RIGOROUS DUPLICATE CHECK: Check for duplicates by normalized name without quality/year
                # Get base name (without quality/year) for aggressive duplicate detection
                nome_base = remove_quality_from_name(nome_normalizado)
                nome_base = re.sub(r'\\s*[\\(\\[]\\d{4}[\\)\\]]\\s*', '', nome_base)
                nome_base = re.sub(r'\\s+', ' ', nome_base).strip().lower()
                
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

"""

# Inserir o código
lines.insert(insert_point, rigorous_check)

# Escrever o novo conteúdo
with open('app/routes/api.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ Verificação rigorosa adicionada ao processo de classificação!")

# Verificar se precisamos adicionar importação e variável
with open('app/routes/api.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
if 'remove_quality_from_name' not in content:
    print("⚠️ Aviso: Precisa adicionar importação de remove_quality_from_name manualmente")
    
if 'total_skipped_rigorous' not in content:
    print("⚠️ Aviso: Precisa adicionar variável total_skipped_rigorous = 0 manualmente")
