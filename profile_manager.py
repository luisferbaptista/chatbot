"""
Sistema de Gestión de Perfiles para el Chatbot
Maneja perfiles, versiones, documentos y contexto para entrenar el bot
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import hashlib


class ProfileManager:
    """Gestor de perfiles del chatbot con versionamiento"""
    
    def __init__(self, profiles_file: str = "bot_profiles.json"):
        self.profiles_file = profiles_file
        self.profiles = self._load_profiles()
    
    def _load_profiles(self) -> Dict:
        """Cargar perfiles desde archivo JSON"""
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error cargando perfiles: {e}")
                return self._create_default_structure()
        return self._create_default_structure()
    
    def _create_default_structure(self) -> Dict:
        """Crear estructura por defecto de perfiles"""
        return {
            "profiles": {},
            "active_profile": None,
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat(),
                "total_profiles": 0
            }
        }
    
    def _save_profiles(self):
        """Guardar perfiles a archivo JSON"""
        self.profiles["metadata"]["last_modified"] = datetime.now().isoformat()
        with open(self.profiles_file, 'w', encoding='utf-8') as f:
            json.dump(self.profiles, f, ensure_ascii=False, indent=2)
    
    def create_profile(self, name: str, description: str = "", profile_type: str = "general") -> Dict:
        """Crear un nuevo perfil"""
        if name in self.profiles["profiles"]:
            raise ValueError(f"El perfil '{name}' ya existe")
        
        profile_id = hashlib.md5(f"{name}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        new_profile = {
            "id": profile_id,
            "name": name,
            "description": description,
            "type": profile_type,
            "created_at": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "active_version": 1,
            "versions": {
                "1": {
                    "version": 1,
                    "created_at": datetime.now().isoformat(),
                    "system_prompt": "",
                    "context": "",
                    "documents": [],
                    "knowledge_base": {},
                    "instructions": [],
                    "examples": [],
                    "restrictions": [],
                    "tone": "profesional",
                    "language": "español"
                }
            },
            "tags": []
        }
        
        self.profiles["profiles"][name] = new_profile
        self.profiles["metadata"]["total_profiles"] += 1
        self._save_profiles()
        
        return new_profile
    
    def get_profile(self, name: str) -> Optional[Dict]:
        """Obtener un perfil por nombre"""
        return self.profiles["profiles"].get(name)
    
    def get_all_profiles(self) -> Dict:
        """Obtener todos los perfiles"""
        return self.profiles["profiles"]
    
    def delete_profile(self, name: str) -> bool:
        """Eliminar un perfil"""
        if name in self.profiles["profiles"]:
            del self.profiles["profiles"][name]
            self.profiles["metadata"]["total_profiles"] -= 1
            
            # Si era el perfil activo, desactivarlo
            if self.profiles["active_profile"] == name:
                self.profiles["active_profile"] = None
            
            self._save_profiles()
            return True
        return False
    
    def update_profile(self, name: str, **kwargs) -> bool:
        """Actualizar información básica del perfil"""
        if name not in self.profiles["profiles"]:
            return False
        
        profile = self.profiles["profiles"][name]
        
        for key, value in kwargs.items():
            if key in ["description", "type", "tags"]:
                profile[key] = value
        
        profile["last_modified"] = datetime.now().isoformat()
        self._save_profiles()
        return True
    
    def create_version(self, profile_name: str, base_version: Optional[int] = None) -> int:
        """Crear una nueva versión del perfil"""
        if profile_name not in self.profiles["profiles"]:
            raise ValueError(f"Perfil '{profile_name}' no encontrado")
        
        profile = self.profiles["profiles"][profile_name]
        versions = profile["versions"]
        
        # Determinar número de nueva versión
        new_version_num = max([int(v) for v in versions.keys()]) + 1
        
        # Si se especifica versión base, copiar de ella, sino de la activa
        if base_version and str(base_version) in versions:
            base_data = versions[str(base_version)].copy()
        else:
            base_data = versions[str(profile["active_version"])].copy()
        
        # Crear nueva versión
        new_version = {
            "version": new_version_num,
            "created_at": datetime.now().isoformat(),
            "system_prompt": base_data.get("system_prompt", ""),
            "context": base_data.get("context", ""),
            "documents": base_data.get("documents", []).copy(),
            "knowledge_base": base_data.get("knowledge_base", {}).copy(),
            "instructions": base_data.get("instructions", []).copy(),
            "examples": base_data.get("examples", []).copy(),
            "restrictions": base_data.get("restrictions", []).copy(),
            "tone": base_data.get("tone", "profesional"),
            "language": base_data.get("language", "español")
        }
        
        profile["versions"][str(new_version_num)] = new_version
        profile["last_modified"] = datetime.now().isoformat()
        self._save_profiles()
        
        return new_version_num
    
    def get_version(self, profile_name: str, version: int) -> Optional[Dict]:
        """Obtener una versión específica del perfil"""
        profile = self.get_profile(profile_name)
        if profile and str(version) in profile["versions"]:
            return profile["versions"][str(version)]
        return None
    
    def activate_version(self, profile_name: str, version: int) -> bool:
        """Activar una versión específica del perfil"""
        if profile_name not in self.profiles["profiles"]:
            return False
        
        profile = self.profiles["profiles"][profile_name]
        if str(version) not in profile["versions"]:
            return False
        
        profile["active_version"] = version
        profile["last_modified"] = datetime.now().isoformat()
        self._save_profiles()
        return True
    
    def delete_version(self, profile_name: str, version: int) -> bool:
        """Eliminar una versión (no se puede eliminar la activa)"""
        if profile_name not in self.profiles["profiles"]:
            return False
        
        profile = self.profiles["profiles"][profile_name]
        
        # No permitir eliminar la versión activa
        if version == profile["active_version"]:
            raise ValueError("No se puede eliminar la versión activa")
        
        # No permitir eliminar si es la única versión
        if len(profile["versions"]) == 1:
            raise ValueError("No se puede eliminar la única versión del perfil")
        
        if str(version) in profile["versions"]:
            del profile["versions"][str(version)]
            profile["last_modified"] = datetime.now().isoformat()
            self._save_profiles()
            return True
        
        return False
    
    def update_version_content(self, profile_name: str, version: int, **kwargs) -> bool:
        """Actualizar el contenido de una versión"""
        version_data = self.get_version(profile_name, version)
        if not version_data:
            return False
        
        for key, value in kwargs.items():
            if key in version_data:
                version_data[key] = value
        
        self.profiles["profiles"][profile_name]["last_modified"] = datetime.now().isoformat()
        self._save_profiles()
        return True
    
    def add_document(self, profile_name: str, version: int, doc_name: str, doc_content: str, doc_type: str = "text") -> bool:
        """Agregar un documento a una versión"""
        version_data = self.get_version(profile_name, version)
        if not version_data:
            return False
        
        document = {
            "name": doc_name,
            "content": doc_content,
            "type": doc_type,
            "added_at": datetime.now().isoformat()
        }
        
        version_data["documents"].append(document)
        self.profiles["profiles"][profile_name]["last_modified"] = datetime.now().isoformat()
        self._save_profiles()
        return True
    
    def remove_document(self, profile_name: str, version: int, doc_index: int) -> bool:
        """Eliminar un documento de una versión"""
        version_data = self.get_version(profile_name, version)
        if not version_data or doc_index >= len(version_data["documents"]):
            return False
        
        version_data["documents"].pop(doc_index)
        self.profiles["profiles"][profile_name]["last_modified"] = datetime.now().isoformat()
        self._save_profiles()
        return True
    
    def add_to_knowledge_base(self, profile_name: str, version: int, key: str, value: str) -> bool:
        """Agregar información a la base de conocimientos"""
        version_data = self.get_version(profile_name, version)
        if not version_data:
            return False
        
        version_data["knowledge_base"][key] = {
            "value": value,
            "added_at": datetime.now().isoformat()
        }
        
        self.profiles["profiles"][profile_name]["last_modified"] = datetime.now().isoformat()
        self._save_profiles()
        return True
    
    def set_active_profile(self, profile_name: str) -> bool:
        """Establecer el perfil activo globalmente"""
        if profile_name not in self.profiles["profiles"]:
            return False
        
        self.profiles["active_profile"] = profile_name
        self._save_profiles()
        return True
    
    def get_active_profile(self) -> Optional[Dict]:
        """Obtener el perfil activo"""
        if self.profiles["active_profile"]:
            return self.get_profile(self.profiles["active_profile"])
        return None
    
    def get_active_profile_context(self) -> str:
        """Obtener el contexto completo del perfil activo para usar en el bot"""
        active_profile = self.get_active_profile()
        if not active_profile:
            return ""
        
        active_version = self.get_version(
            active_profile["name"], 
            active_profile["active_version"]
        )
        
        if not active_version:
            return ""
        
        # Construir contexto completo
        context_parts = []
        
        # System prompt
        if active_version.get("system_prompt"):
            context_parts.append(f"SYSTEM PROMPT:\n{active_version['system_prompt']}\n")
        
        # Contexto general
        if active_version.get("context"):
            context_parts.append(f"CONTEXTO:\n{active_version['context']}\n")
        
        # Instrucciones
        if active_version.get("instructions"):
            context_parts.append("INSTRUCCIONES:")
            for idx, instruction in enumerate(active_version["instructions"], 1):
                context_parts.append(f"{idx}. {instruction}")
            context_parts.append("")
        
        # Base de conocimientos
        if active_version.get("knowledge_base"):
            context_parts.append("BASE DE CONOCIMIENTOS:")
            for key, data in active_version["knowledge_base"].items():
                context_parts.append(f"• {key}: {data['value']}")
            context_parts.append("")
        
        # Ejemplos
        if active_version.get("examples"):
            context_parts.append("EJEMPLOS:")
            for example in active_version["examples"]:
                context_parts.append(f"• {example}")
            context_parts.append("")
        
        # Restricciones
        if active_version.get("restrictions"):
            context_parts.append("RESTRICCIONES:")
            for restriction in active_version["restrictions"]:
                context_parts.append(f"• {restriction}")
            context_parts.append("")
        
        # Documentos
        if active_version.get("documents"):
            context_parts.append("DOCUMENTOS DE REFERENCIA:")
            for doc in active_version["documents"]:
                context_parts.append(f"\n--- {doc['name']} ---")
                context_parts.append(doc['content'])
            context_parts.append("")
        
        # Tono y lenguaje
        context_parts.append(f"TONO: {active_version.get('tone', 'profesional')}")
        context_parts.append(f"IDIOMA: {active_version.get('language', 'español')}")
        
        return "\n".join(context_parts)
    
    def export_profile(self, profile_name: str, export_path: str) -> bool:
        """Exportar un perfil a archivo JSON"""
        profile = self.get_profile(profile_name)
        if not profile:
            return False
        
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)
        
        return True
    
    def import_profile(self, import_path: str) -> Optional[str]:
        """Importar un perfil desde archivo JSON"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            profile_name = profile_data["name"]
            
            # Si ya existe, agregar sufijo
            original_name = profile_name
            counter = 1
            while profile_name in self.profiles["profiles"]:
                profile_name = f"{original_name}_{counter}"
                counter += 1
            
            profile_data["name"] = profile_name
            self.profiles["profiles"][profile_name] = profile_data
            self.profiles["metadata"]["total_profiles"] += 1
            self._save_profiles()
            
            return profile_name
        except Exception as e:
            print(f"Error importando perfil: {e}")
            return None

