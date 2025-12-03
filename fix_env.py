"""
Script para verificar e corrigir o arquivo .env com o modelo correto.
"""
import os
from pathlib import Path

def fix_env():
    """Verifica e corrige o arquivo .env"""
    env_path = Path(".env")
    env_example_path = Path("env.example")
    
    print("🔍 Verificando arquivo .env...")
    
    if not env_path.exists():
        print("❌ Arquivo .env não encontrado!")
        if env_example_path.exists():
            print("📋 Copiando env.example para .env...")
            import shutil
            shutil.copy(env_example_path, env_path)
            print("✅ Arquivo .env criado!")
        else:
            print("❌ Arquivo env.example também não encontrado!")
            return False
    
    # Lê o arquivo .env
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Verifica e corrige LLM_MODEL
    fixed = False
    new_lines = []
    llm_model_found = False
    
    for line in lines:
        if line.strip().startswith("LLM_MODEL="):
            llm_model_found = True
            current_value = line.split("=", 1)[1].strip()
            
            # Verifica se está usando modelo inválido
            if current_value in ["gemini-1.5-flash", "gemini-2.5-flash", "gemini-1.5-flash-002"]:
                if current_value != "gemini-1.5-flash-002":
                    print(f"⚠️  Modelo inválido encontrado: {current_value}")
                    print("✅ Corrigindo para: gemini-1.5-flash-002")
                    new_lines.append("LLM_MODEL=gemini-1.5-flash-002\n")
                    fixed = True
                else:
                    print(f"✅ Modelo correto já configurado: {current_value}")
                    new_lines.append(line)
            else:
                # Modelo customizado, mantém
                print(f"ℹ️  Modelo customizado encontrado: {current_value}")
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    # Se LLM_MODEL não foi encontrado, adiciona
    if not llm_model_found:
        print("⚠️  LLM_MODEL não encontrado no .env")
        print("✅ Adicionando LLM_MODEL=gemini-1.5-flash-002")
        # Adiciona após API_KEY se existir
        inserted = False
        final_lines = []
        for i, line in enumerate(new_lines):
            final_lines.append(line)
            if not inserted and "API_KEY=" in line and i < len(new_lines) - 1:
                # Adiciona LLM_MODEL após API_KEY
                final_lines.append("\n")
                final_lines.append("# Modelo do LLM\n")
                final_lines.append("LLM_MODEL=gemini-1.5-flash-002\n")
                inserted = True
        if not inserted:
            final_lines.append("\n# Modelo do LLM\n")
            final_lines.append("LLM_MODEL=gemini-1.5-flash-002\n")
        new_lines = final_lines
        fixed = True
    
    # Salva se houve mudanças
    if fixed:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print("\n✅ Arquivo .env corrigido e salvo!")
        return True
    else:
        print("\n✅ Arquivo .env já está correto!")
        return True

if __name__ == "__main__":
    print("=" * 60)
    print("  CORREÇÃO DO ARQUIVO .ENV")
    print("=" * 60 + "\n")
    fix_env()
    print("\n" + "=" * 60)
    print("✅ Processo concluído!")
    print("=" * 60)

