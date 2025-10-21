"""
Script para cambiar contraseñas de usuarios
"""
import json
import hashlib
import os

AUTH_FILE = "auth_config.json"

def hash_password(password):
    """Hash de contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_auth():
    if os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"users": {}}

def save_auth(config):
    with open(AUTH_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def change_password():
    print("="*50)
    print(" CAMBIO DE CONTRASEÑA - Sistema de Gestión Bot")
    print("="*50)
    print()
    
    config = load_auth()
    
    # Mostrar usuarios disponibles
    print("Usuarios disponibles:")
    for idx, username in enumerate(config["users"].keys(), 1):
        print(f"{idx}. {username}")
    print()
    
    username = input("Ingrese nombre de usuario: ").strip()
    
    if username not in config["users"]:
        print(f"\n❌ Usuario '{username}' no encontrado.")
        
        # Opción de crear nuevo usuario
        crear = input("\n¿Desea crear este usuario? (s/n): ").strip().lower()
        if crear == 's':
            role = input("Rol (admin/user): ").strip() or "user"
            config["users"][username] = {
                "password": "",
                "role": role,
                "created_at": "2025-01-01T00:00:00"
            }
        else:
            return
    
    # Cambiar contraseña
    new_password = input("Nueva contraseña: ").strip()
    confirm_password = input("Confirmar contraseña: ").strip()
    
    if new_password != confirm_password:
        print("\n❌ Las contraseñas no coinciden.")
        return
    
    if len(new_password) < 6:
        print("\n❌ La contraseña debe tener al menos 6 caracteres.")
        return
    
    # Guardar contraseña hasheada
    config["users"][username]["password"] = hash_password(new_password)
    save_auth(config)
    
    print(f"\n✅ Contraseña cambiada exitosamente para '{username}'")
    print()

if __name__ == "__main__":
    try:
        change_password()
    except KeyboardInterrupt:
        print("\n\nOperación cancelada.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

