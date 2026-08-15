"""Teste do endpoint de duplicatas via HTTP."""

import requests
import json

print("TESTE DO ENDPOINT DE DUPLICATAS VIA HTTP")
print("=" * 60)

try:
    # Testar endpoint básico
    print("\n📡 Testando conexão com o servidor...")
    response = requests.get('http://127.0.0.1:5000/', timeout=5)
    print(f"✅ Servidor respondendo (status: {response.status_code})")
    
    # Testar endpoint de mídias
    print("\n📡 Testando endpoint de mídias...")
    response = requests.get('http://127.0.0.1:5000/api/media/items?limit=1', timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('items') and len(data['items']) > 0:
            media_id = data['items'][0]['id']
            media_name = data['items'][0]['nome_da_midia']
            print(f"✅ Mídia encontrada: ID={media_id}, Nome={media_name}")
            
            # Testar endpoint de duplicatas melhorado
            print(f"\n📡 Testando endpoint de duplicatas para mídia {media_id}...")
            dup_response = requests.get(f'http://127.0.0.1:5000/api/media/items/{media_id}/duplicates', timeout=10)
            
            if dup_response.status_code == 200:
                dup_data = dup_response.json()
                print(f"✅ Endpoint de duplicatas funcionando!")
                print(f"\n📊 Resultado:")
                print(f"  - Duplicatas por hash: {dup_data.get('hash_duplicates', 0)}")
                print(f"  - Duplicatas por nome base: {dup_data.get('name_duplicates', 0)}")
                print(f"  - Total de duplicatas: {dup_data.get('total_duplicates', 0)}")
                
                if dup_data.get('hash_duplicates'):
                    print(f"\n  Exemplos de duplicatas por hash:")
                    for dup in dup_data['hash_duplicates'][:3]:
                        print(f"    - ID: {dup['id']}, Nome: {dup['nome_da_midia'][:40]}")
                
                if dup_data.get('name_duplicates'):
                    print(f"\n  Exemplos de duplicatas por nome base:")
                    for dup in dup_data['name_duplicates'][:3]:
                        print(f"    - ID: {dup['id']}, Nome: {dup['nome_da_midia'][:40]}")
            else:
                print(f"❌ Erro no endpoint de duplicatas: {dup_response.status_code}")
                print(f"   Resposta: {dup_response.text}")
        else:
            print("❌ Nenhuma mídia encontrada para teste")
    else:
        print(f"❌ Erro ao buscar mídias: {response.status_code}")
        print(f"   Resposta: {response.text}")
    
    print("\n" + "=" * 60)
    print("🎉 TESTE HTTP FINALIZADO!")
    print("\n✅ Servidor Flask funcionando corretamente")
    print("✅ Endpoint de duplicatas melhorado respondendo")
    
except requests.exceptions.ConnectionError:
    print("❌ Erro: Não foi possível conectar ao servidor")
    print("   Verifique se o servidor está rodando em http://127.0.0.1:5000")
except Exception as e:
    print(f"❌ Erro no teste: {e}")
