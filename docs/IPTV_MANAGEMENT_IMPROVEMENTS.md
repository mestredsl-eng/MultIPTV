# Melhorias no Gerenciamento de IPTV

## Visão Geral

Este documento descreve as melhorias implementadas na página de cadastro e gerenciamento de fontes IPTV, incluindo correção de bugs e novas funcionalidades.

## Problemas Corrigidos

### 1. Bug de Remoção Incompleta de IPTV

**Problema**: Ao remover uma IPTV, o sistema dizia que apagou mas não apagava realmente.

**Causa Raiz**:
- A função `delete_iptv` estava fazendo "soft delete" (apenas desativando com `ativo = 0`)
- Não removia mídias do banco de dados
- Não removia arquivos .strm da galeria

**Solução**:
- Alterado para "hard delete" - remove completamente do banco de dados
- Remove todas as mídias associadas da tabela `midias`
- Remove arquivos .strm da galeria usando função `generate_file_path`
- Feedback detalhado ao usuário com contagem de mídias e arquivos removidos

**Arquivos**:
- `app/database/queries.py` - Função `delete_iptv()` atualizada
- `app/routes/api.py` - Endpoint DELETE retorna informações de arquivos removidos
- `app/templates/registration.html` - Feedback detalhado ao usuário

**Exemplo de Feedback**:
```
IPTV removida com sucesso!
- 150 mídias removidas do banco de dados
- 120 arquivos .strm removidos da galeria
```

**Impacto**: Agora ao remover uma IPTV, ela é completamente limpa: banco de dados + galeria.

### 2. Erros JavaScript na Página de Cadastro

**Problema**: Script tinha erros quando nomes de IPTV continham aspas (ex: "João's IPTV").

**Causa Raiz**:
- Nomes com aspas simples ou duplas quebravam o código JavaScript nos eventos `onclick`
- Não havia escape de caracteres especiais

**Solução**:
- Adicionado escape de aspas simples e duplas no nome antes de passar para funções JavaScript
- Previne erros de sintaxe quando há aspas nos nomes

**Arquivos**:
- `app/templates/registration.html` - Escape de aspas adicionado

**Código**:
```javascript
// Escapar nome para evitar problemas com aspas
const escapedNome = iptv.nome.replace(/'/g, "\\'").replace(/"/g, '\\"');

// Usar nome escapado nos eventos onclick
onclick="testIptvConnection(${iptv.id}, '${escapedNome}')"
```

**Impacto**: Página de cadastro funciona corretamente com qualquer nome de IPTV.

## Novas Funcionalidades

### 1. Teste de Conexão IPTV

**Problema**: Usuário não tinha como testar se uma IPTV estava realmente funcionando antes de usá-la.

**Solução**:
- Adicionado botão "Testar" para cada IPTV na página de cadastro
- Testa até 5 mídias ativas da IPTV usando requests (HEAD request)
- Calcula taxa de sucesso e determina status (online/offline)
- Atualiza timestamp de última atualização
- Feedback visual com badge colorido e estatísticas

**Arquivos**:
- `app/routes/api.py` - Novo endpoint `/api/iptv/sources/<iptv_id>/test-connection`
- `app/templates/registration.html` - Nova coluna "Conexão" e botão de teste
- JavaScript - Função `testIptvConnection()` com feedback visual

**Endpoint API**:
```python
@bp.route('/iptv/sources/<int:iptv_id>/test-connection', methods=['POST'])
def test_iptv_connection(iptv_id):
    """Test IPTV connection by checking if media streams are accessible."""
    # Get IPTV source info
    iptv = db.execute('SELECT * FROM iptvs WHERE id = ?', (iptv_id,)).fetchone()
    
    # Get a sample of active media from this IPTV
    media_samples = db.execute(
        'SELECT url FROM midias WHERE iptv_id = ? AND status = 1 AND black_list = 0 LIMIT 5',
        (iptv_id,)
    ).fetchall()
    
    # Test each media URL
    for media in media_samples:
        response = requests.head(url, timeout=10, allow_redirects=True)
        
        if response.status_code in [200, 206, 302, 301]:
            success_count += 1
    
    # Determine overall status
    success_rate = (success_count / tested_count) * 100 if tested_count > 0 else 0
    
    return jsonify({
        'success': True,
        'status': 'online' if success_rate > 50 else 'offline',
        'tested_count': tested_count,
        'success_count': success_count,
        'success_rate': success_rate,
        'message': f'{success_count}/{tested_count} mídias acessíveis ({success_rate:.1f}%)'
    })
```

**Interface Visual**:
- Botão desabilitado durante o teste
- Mostra spinner enquanto testa
- Exibe badge colorido após resultado:
  - 🟢 Verde: Online (mais de 50% das mídias acessíveis)
  - 🔴 Vermelho: Offline (menos de 50% acessíveis)
  - ⚠️ Amarelo: Erro ou sem mídia

**Impacto**: Usuário pode verificar se IPTVs estão funcionando em tempo real.

## Melhorias na Interface

### Nova Coluna "Conexão"

Adicionada nova coluna na tabela de fontes IPTV:
- **Botão "Testar"**: Inicia teste de conexão
- **Badge de Status**: Mostra resultado do teste
- **Feedback Visual**: Spinner durante teste, badge colorido após resultado

### Feedback Detalhado de Remoção

Melhorado feedback ao remover IPTV:
- Contagem de mídias removidas do banco de dados
- Contagem de arquivos .strm removidos da galeria
- Mensagem clara e informativa

### Tratamento de Erros

Melhorado tratamento de erros:
- Escape de aspas para evitar erros JavaScript
- Validação de elementos HTML com fallback
- Tratamento de erros com alertas ao usuário

## Compatibilidade

### Compatibilidade de get_movie_info

Atualizadas todas as chamadas do `get_movie_info` para passar o parâmetro `categoria`:
- `app/routes/api.py` - Endpoints de enriquecimento
- `app/services/tmdb_validator.py` - Validação TMDB
- `app/services/bulk_classifier.py` - Classificação em lote

### Compatibilidade de Remoção

Atualizado endpoint DELETE para retornar informações de arquivos removidos:
- `affected_media`: Número de mídias removidas do banco
- `files_removed`: Número de arquivos .strm removidos da galeria

## Testes e Validação

### Teste de Remoção
- ✅ Verificado que remoção agora deleta completamente
- ✅ Arquivos .strm são removidos da galeria
- ✅ Feedback detalhado ao usuário
- ✅ Mídias são removidas do banco de dados

### Teste de Conexão
- ✅ Botão de teste funciona corretamente
- ✅ Feedback visual claro com estatísticas
- ✅ Atualiza timestamp de última atualização
- ✅ Determina status online/offline corretamente

### Teste de JavaScript
- ✅ Nomes com aspas funcionam corretamente
- ✅ Não há erros de sintaxe JavaScript
- ✅ Funciona com caracteres especiais

## Uso da Interface

### Testar Conexão IPTV

1. Vá para a página de Cadastro
2. Encontre a IPTV que deseja testar
3. Clique no botão "Testar" na coluna "Conexão"
4. Aguarde o teste (aprox. 10-30 segundos)
5. Veja o resultado no badge ao lado do botão

### Remover IPTV

1. Vá para a página de Cadastro
2. Clique no botão "Remover" da IPTV desejada
3. Digite o nome da IPTV para confirmar
4. Clique em "Confirmar"
5. Veja o feedback detalhado da remoção

## Resumo

As melhorias implementadas resolveram os problemas principais no gerenciamento de IPTV:

1. **Remoção correta**: IPTVs são completamente removidas (banco + galeria)
2. **Teste de conexão**: Usuário pode verificar se IPTVs estão funcionando
3. **JavaScript estável**: Funciona com qualquer nome de IPTV
4. **Feedback claro**: Informações detalhadas de todas as operações

A página de cadastro agora é mais robusta e confiável para gerenciar múltiplas fontes IPTV.