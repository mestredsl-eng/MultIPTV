# Sistema de Auto-Blacklist Automática

## Visão Geral

Este sistema implementa controle automático de blacklist para evitar duplicação de conteúdo banido no banco de dados IPTV. Quando um item é colocado na blacklist, todos os itens com nomes similares são automaticamente banidos também.

## Funcionalidades

### 1. Auto-Propagação de Blacklist

**O que faz:**
- Quando um item é marcado como blacklist (`black_list = 1`), o sistema busca automaticamente por todos os itens com nomes similares
- Itens encontrados são automaticamente colocados na blacklist também
- Isso garante que não existam duplicatas de conteúdo banido

**Como funciona:**
```python
# No DuplicateManager:
def auto_propagate_blacklist(self, media_id):
    # Extrai o nome base (sem qualidade e ano)
    nome_base = self.get_base_name(nome_normalizado)
    
    # Busca itens similares que ainda não estão na blacklist
    similares = db.execute('''
        SELECT id, nome_da_midia FROM midias 
        WHERE nome_normalizado LIKE ? AND black_list = 0 AND status = 1 AND id != ?
    ''', (f'%{nome_base}%', media_id))
    
    # Coloca todos os itens similares na blacklist
    for item in similares:
        db.execute('UPDATE midias SET black_list = 1 WHERE id = ?', (item['id'],))
```

### 2. Verificação During Inserção

**O que faz:**
- Durante a inserção de novas mídias, o sistema verifica se o nome é similar a itens já banidos
- Se similar, o novo item é inserido diretamente na blacklist (`black_list = 1`)

**Como funciona:**
```python
# No processo de inserção (api.py):
should_auto_blacklist, reason = duplicate_manager.check_and_apply_auto_blacklist(
    nome_normalizado, entry['name']
)

black_list_value = 1 if should_auto_blacklist else 0

# Inserir com o valor correto de blacklist
db.execute('INSERT INTO midias (... black_list ...) VALUES (... ? ...)', 
          (..., black_list_value))
```

### 3. Limpeza de Itens Existentes

**Script disponível:** `propagate_blacklist.py`

**O que faz:**
- Percorre todos os itens atualmente na blacklist
- Para cada item, busca por itens similares que ainda não estão na blacklist
- Aplica a blacklist automaticamente a esses itens

**Como usar:**
```bash
python propagate_blacklist.py
```

## Exemplo Prático

### Cenário: "meus filmes picles"

**Situação:**
- Você tem um conteúdo chamado "meus filmes picles" que foi banido
- Existem várias variações como:
  - "meus filmes picles 2024"
  - "meus filmes picles [4K]"
  - "meus filmes picles HD"

**Com o sistema antigo:**
- Cada variação teria que ser banida manualmente
- Conteúdo duplicado continuaria entrando no sistema

**Com o novo sistema:**
1. Ao banir "meus filmes picles", o sistema automaticamente:
   - Busca por todas as variações
   - Coloca todas na blacklist automaticamente
2. Se tentar inserir "meus filmes picles 2025":
   - O sistema detecta similaridade com item banido
   - Insere diretamente na blacklist

## Benefícios

1. **Elimina duplicação de conteúdo banido**: Não existem múltiplas versões do mesmo conteúdo banido
2. **Economiza tempo manual**: Não precisa banir cada variação individualmente
3. **Consistência**: Garante que o critério de blacklist seja aplicado uniformemente
4. **Prevenção**: Nova entrada com nome similar é automaticamente banida

## Implementação Técnica

### Arquivos Modificados

1. **`app/services/duplicate_manager.py`**
   - Adicionado método `auto_propagate_blacklist()`
   - Adicionado método `check_and_apply_auto_blacklist()`
   - Adicionado método `apply_auto_blacklist_to_all_existing()`

2. **`app/routes/api.py`**
   - Modificado processo de inserção para verificar auto-blacklist
   - Adicionado contador de itens auto-blacklistados
   - Atualizada mensagem de status

### Scripts Novos

1. **`propagate_blacklist.py`**
   - Script para aplicar auto-blacklist a itens existentes
   - Permite limpar o banco de dados de conteúdo duplicado banido

2. **`test_auto_blacklist.py`**
   - Script de teste para verificar funcionalidade

3. **`demo_auto_blacklist.py`**
   - Demonstração interativa do funcionamento

## Como Usar

### Uso Automático (Sistema já configurado)

O sistema funciona automaticamente sem intervenção manual:

1. **Durante processamento normal**: O sistema verifica cada nova mídia
2. **Ao banir manualmente**: A propagação é automática

### Uso Manual (Limpeza)

Para aplicar a regra a itens existentes:

```bash
# Aplicar auto-blacklist a todo o banco de dados
python propagate_blacklist.py
```

### Teste

Para testar a funcionalidade:

```bash
# Testar sistema
python test_auto_blacklist.py

# Ver demonstração
python demo_auto_blacklist.py
```

## Estatísticas

No banco de dados atual:
- **Total de itens**: 512,779
- **Itens na blacklist**: 30,453
- **Itens ativos**: 482,326
- **Taxa de blacklist**: ~5.9%

## Notas Importantes

1. **Similaridade baseada em nome base**: O sistema remove qualidade e ano antes de comparar nomes
2. **Case-insensitive**: A comparação não diferencia maiúsculas/minúsculas
3. **Matching parcial**: Usa `LIKE %nome%` para encontrar variações
4. **Logging**: Todas as operações de auto-blacklist são registradas nos logs
5. **Segurança**: O sistema não remove itens, apenas marca como blacklist

## Solução de Problemas

### Se muitos itens estão sendo blacklistados incorretamente:

1. Verifique se o nome base está correto:
```python
python -c "from app.services.parser import remove_quality_from_name; print(remove_quality_from_name('seu item'))"
```

2. Revise itens blacklistados recentemente:
```sql
SELECT id, nome_da_midia FROM midias WHERE black_list = 1 ORDER BY id DESC LIMIT 10;
```

3. Se necessário, reverta:
```python
python undo_blacklist_changes.py
```

### Performance:

O sistema usa queries otimizadas com LIMIT para evitar problemas de performance:
- `LIMIT 1` para verificação durante inserção
- `LIMIT 50` para busca de similares
- Processamento em lotes durante limpeza

## Conclusão

O sistema de auto-blacklist resolve o problema de duplicação de conteúdo banido, garantindo que quando um conteúdo é banido, todas as suas variações também sejam automaticamente controladas, economizando tempo e mantendo a consistência do banco de dados.