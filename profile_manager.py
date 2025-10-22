"""
Sistema de Gestión de Perfiles para el Chatbot
Maneja perfiles, versiones, documentos y contexto para entrenar el bot
Soporta múltiples perfiles activos con prioridades y carga/exportación CSV
"""

import json
import os
import csv
from datetime import datetime
from typing import Dict, List, Optional, Tuple
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
            "active_profile": None,  # Mantener por retrocompatibilidad
            "active_profiles": [],  # Nuevo: lista de {name, priority}
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
    
    # ===== GESTIÓN DE MÚLTIPLES PERFILES ACTIVOS CON PRIORIDADES =====
    
    def add_active_profile(self, profile_name: str, priority: int = 1) -> bool:
        """Agregar un perfil a la lista de perfiles activos con prioridad
        
        Args:
            profile_name: Nombre del perfil a activar
            priority: Prioridad del perfil (1=mayor prioridad, números mayores=menor prioridad)
        
        Returns:
            True si se agregó exitosamente, False en caso contrario
        """
        if profile_name not in self.profiles["profiles"]:
            return False
        
        # Inicializar active_profiles si no existe (retrocompatibilidad)
        if "active_profiles" not in self.profiles:
            self.profiles["active_profiles"] = []
        
        # Verificar si el perfil ya está activo
        for active in self.profiles["active_profiles"]:
            if active["name"] == profile_name:
                # Actualizar solo la prioridad si ya existe
                active["priority"] = priority
                self._save_profiles()
                return True
        
        # Agregar nuevo perfil activo
        self.profiles["active_profiles"].append({
            "name": profile_name,
            "priority": priority,
            "activated_at": datetime.now().isoformat()
        })
        
        # Ordenar por prioridad (menor número = mayor prioridad)
        self.profiles["active_profiles"].sort(key=lambda x: x["priority"])
        
        # Mantener compatibilidad: actualizar active_profile al de mayor prioridad
        if self.profiles["active_profiles"]:
            self.profiles["active_profile"] = self.profiles["active_profiles"][0]["name"]
        
        self._save_profiles()
        return True
    
    def remove_active_profile(self, profile_name: str) -> bool:
        """Remover un perfil de la lista de perfiles activos
        
        Args:
            profile_name: Nombre del perfil a desactivar
        
        Returns:
            True si se removió exitosamente, False si no estaba activo
        """
        if "active_profiles" not in self.profiles:
            self.profiles["active_profiles"] = []
        
        initial_length = len(self.profiles["active_profiles"])
        self.profiles["active_profiles"] = [
            p for p in self.profiles["active_profiles"] 
            if p["name"] != profile_name
        ]
        
        # Actualizar active_profile para retrocompatibilidad
        if self.profiles["active_profiles"]:
            self.profiles["active_profile"] = self.profiles["active_profiles"][0]["name"]
        else:
            self.profiles["active_profile"] = None
        
        if len(self.profiles["active_profiles"]) < initial_length:
            self._save_profiles()
            return True
        
        return False
    
    def get_active_profiles(self) -> List[Dict]:
        """Obtener lista de perfiles activos ordenados por prioridad
        
        Returns:
            Lista de diccionarios con {name, priority, activated_at}
        """
        if "active_profiles" not in self.profiles:
            self.profiles["active_profiles"] = []
        
        return self.profiles["active_profiles"]
    
    def set_profile_priority(self, profile_name: str, new_priority: int) -> bool:
        """Cambiar la prioridad de un perfil activo
        
        Args:
            profile_name: Nombre del perfil
            new_priority: Nueva prioridad (1=mayor, números mayores=menor)
        
        Returns:
            True si se actualizó, False si el perfil no está activo
        """
        if "active_profiles" not in self.profiles:
            self.profiles["active_profiles"] = []
        
        updated = False
        for active in self.profiles["active_profiles"]:
            if active["name"] == profile_name:
                active["priority"] = new_priority
                updated = True
                break
        
        if updated:
            # Reordenar por prioridad
            self.profiles["active_profiles"].sort(key=lambda x: x["priority"])
            
            # Actualizar active_profile para retrocompatibilidad
            if self.profiles["active_profiles"]:
                self.profiles["active_profile"] = self.profiles["active_profiles"][0]["name"]
            
            self._save_profiles()
            return True
        
        return False
    
    def clear_active_profiles(self):
        """Desactivar todos los perfiles"""
        self.profiles["active_profiles"] = []
        self.profiles["active_profile"] = None
        self._save_profiles()
    
    def get_multi_profile_context(self) -> str:
        """Obtener el contexto combinado de todos los perfiles activos según prioridad
        
        Los perfiles se combinan jerárquicamente:
        - El perfil de mayor prioridad (1) se aplica primero
        - Los perfiles de menor prioridad complementan/extienden el contexto
        
        Returns:
            Contexto combinado de todos los perfiles activos
        """
        if "active_profiles" not in self.profiles or not self.profiles["active_profiles"]:
            # Fallback a método original para retrocompatibilidad
            return self.get_active_profile_context()
        
        active_profiles = self.get_active_profiles()
        
        if not active_profiles:
            return ""
        
        # Construir contexto combinado
        combined_parts = []
        
        # Header indicando perfiles activos
        if len(active_profiles) > 1:
            combined_parts.append("=" * 80)
            combined_parts.append("CONFIGURACIÓN DE PERFILES MÚLTIPLES")
            combined_parts.append("Los siguientes perfiles están activos con sus prioridades:")
            for ap in active_profiles:
                combined_parts.append(f"  • {ap['name']} (Prioridad: {ap['priority']})")
            combined_parts.append("=" * 80)
            combined_parts.append("")
        
        # Procesar cada perfil según prioridad
        for idx, active_prof in enumerate(active_profiles):
            profile = self.get_profile(active_prof["name"])
            if not profile:
                continue
            
            version = self.get_version(profile["name"], profile["active_version"])
            if not version:
                continue
            
            priority = active_prof["priority"]
            profile_name = active_prof["name"]
            
            # Separador de perfil
            if len(active_profiles) > 1:
                combined_parts.append("")
                combined_parts.append("=" * 80)
                combined_parts.append(f"PERFIL: {profile_name} | PRIORIDAD: {priority}")
                combined_parts.append("=" * 80)
                combined_parts.append("")
            
            # System prompt
            if version.get("system_prompt"):
                if idx == 0:  # Solo el perfil principal tiene system prompt
                    combined_parts.append(f"SYSTEM PROMPT:\n{version['system_prompt']}\n")
                else:
                    combined_parts.append(f"CONTEXTO ADICIONAL ({profile_name}):\n{version['system_prompt']}\n")
            
            # Contexto general
            if version.get("context"):
                combined_parts.append(f"CONTEXTO:\n{version['context']}\n")
            
            # Instrucciones
            if version.get("instructions"):
                combined_parts.append(f"INSTRUCCIONES ({profile_name}):")
                for idx_inst, instruction in enumerate(version["instructions"], 1):
                    combined_parts.append(f"{idx_inst}. {instruction}")
                combined_parts.append("")
            
            # Base de conocimientos
            if version.get("knowledge_base"):
                combined_parts.append(f"BASE DE CONOCIMIENTOS ({profile_name}):")
                for key, data in version["knowledge_base"].items():
                    combined_parts.append(f"• {key}: {data['value']}")
                combined_parts.append("")
            
            # Ejemplos
            if version.get("examples"):
                combined_parts.append(f"EJEMPLOS ({profile_name}):")
                for example in version["examples"]:
                    combined_parts.append(f"• {example}")
                combined_parts.append("")
            
            # Restricciones
            if version.get("restrictions"):
                combined_parts.append(f"RESTRICCIONES ({profile_name}):")
                for restriction in version["restrictions"]:
                    combined_parts.append(f"• {restriction}")
                combined_parts.append("")
            
            # Documentos
            if version.get("documents"):
                combined_parts.append(f"DOCUMENTOS DE REFERENCIA ({profile_name}):")
                for doc in version["documents"]:
                    combined_parts.append(f"\n--- {doc['name']} ---")
                    combined_parts.append(doc['content'])
                combined_parts.append("")
        
        # Tono y lenguaje del perfil principal
        if active_profiles:
            main_profile = self.get_profile(active_profiles[0]["name"])
            if main_profile:
                main_version = self.get_version(main_profile["name"], main_profile["active_version"])
                if main_version:
                    combined_parts.append("")
                    combined_parts.append("=" * 80)
                    combined_parts.append(f"TONO PRINCIPAL: {main_version.get('tone', 'profesional')}")
                    combined_parts.append(f"IDIOMA PRINCIPAL: {main_version.get('language', 'español')}")
                    combined_parts.append("=" * 80)
        
        return "\n".join(combined_parts)
    
    # ===== IMPORTACIÓN Y EXPORTACIÓN CSV =====
    
    def export_profile_to_csv(self, profile_name: str, csv_path: str) -> bool:
        """Exportar un perfil a formato CSV
        
        El CSV incluirá la versión activa del perfil con todos sus componentes
        
        Args:
            profile_name: Nombre del perfil a exportar
            csv_path: Ruta del archivo CSV de destino
        
        Returns:
            True si se exportó exitosamente
        """
        profile = self.get_profile(profile_name)
        if not profile:
            return False
        
        version = self.get_version(profile_name, profile["active_version"])
        if not version:
            return False
        
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow(['Campo', 'Valor'])
                
                # Metadata del perfil
                writer.writerow(['profile_name', profile['name']])
                writer.writerow(['profile_description', profile.get('description', '')])
                writer.writerow(['profile_type', profile.get('type', 'general')])
                writer.writerow(['profile_id', profile.get('id', '')])
                writer.writerow(['active_version', profile.get('active_version', 1)])
                
                # Datos de la versión
                writer.writerow(['system_prompt', version.get('system_prompt', '')])
                writer.writerow(['context', version.get('context', '')])
                writer.writerow(['tone', version.get('tone', 'profesional')])
                writer.writerow(['language', version.get('language', 'español')])
                
                # Instrucciones (separadas por |)
                instructions = version.get('instructions', [])
                writer.writerow(['instructions', '|'.join(instructions)])
                
                # Ejemplos (separados por ||)
                examples = version.get('examples', [])
                writer.writerow(['examples', '||'.join(examples)])
                
                # Restricciones (separadas por |)
                restrictions = version.get('restrictions', [])
                writer.writerow(['restrictions', '|'.join(restrictions)])
                
                # Base de conocimientos (formato: key1=value1|key2=value2)
                kb = version.get('knowledge_base', {})
                kb_str = '|'.join([f"{k}={v['value']}" for k, v in kb.items()])
                writer.writerow(['knowledge_base', kb_str])
                
                # Documentos (formato: name1::content1||name2::content2)
                docs = version.get('documents', [])
                docs_str = '||'.join([f"{doc['name']}::{doc['content']}" for doc in docs])
                writer.writerow(['documents', docs_str])
            
            return True
        except Exception as e:
            print(f"Error exportando a CSV: {e}")
            return False
    
    def import_profile_from_csv(self, csv_path: str) -> Optional[str]:
        """Importar un perfil desde archivo CSV
        
        Args:
            csv_path: Ruta del archivo CSV a importar
        
        Returns:
            Nombre del perfil importado o None si hubo error
        """
        try:
            data = {}
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                
                for row in reader:
                    if len(row) >= 2:
                        data[row[0]] = row[1]
            
            # Crear perfil
            profile_name = data.get('profile_name', 'Imported Profile')
            description = data.get('profile_description', '')
            profile_type = data.get('profile_type', 'general')
            
            # Verificar si ya existe y agregar sufijo
            original_name = profile_name
            counter = 1
            while profile_name in self.profiles["profiles"]:
                profile_name = f"{original_name}_{counter}"
                counter += 1
            
            # Crear el perfil
            profile = self.create_profile(profile_name, description, profile_type)
            
            # Actualizar versión 1 con los datos del CSV
            version_data = {
                'system_prompt': data.get('system_prompt', ''),
                'context': data.get('context', ''),
                'tone': data.get('tone', 'profesional'),
                'language': data.get('language', 'español'),
                'instructions': data.get('instructions', '').split('|') if data.get('instructions') else [],
                'examples': data.get('examples', '').split('||') if data.get('examples') else [],
                'restrictions': data.get('restrictions', '').split('|') if data.get('restrictions') else [],
            }
            
            # Filtrar valores vacíos
            version_data['instructions'] = [i for i in version_data['instructions'] if i.strip()]
            version_data['examples'] = [e for e in version_data['examples'] if e.strip()]
            version_data['restrictions'] = [r for r in version_data['restrictions'] if r.strip()]
            
            # Knowledge base
            kb_str = data.get('knowledge_base', '')
            if kb_str:
                for kb_item in kb_str.split('|'):
                    if '=' in kb_item:
                        key, value = kb_item.split('=', 1)
                        self.add_to_knowledge_base(profile_name, 1, key, value)
            
            # Documentos
            docs_str = data.get('documents', '')
            if docs_str:
                for doc_item in docs_str.split('||'):
                    if '::' in doc_item:
                        doc_name, doc_content = doc_item.split('::', 1)
                        self.add_document(profile_name, 1, doc_name, doc_content, 'text')
            
            # Actualizar versión con los datos
            self.update_version_content(profile_name, 1, **version_data)
            
            return profile_name
            
        except Exception as e:
            print(f"Error importando desde CSV: {e}")
            return None
    
    def export_all_profiles_to_csv(self, csv_path: str) -> bool:
        """Exportar todos los perfiles a un archivo CSV consolidado
        
        Args:
            csv_path: Ruta del archivo CSV de destino
        
        Returns:
            True si se exportó exitosamente
        """
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow([
                    'profile_name', 'profile_description', 'profile_type', 
                    'system_prompt', 'context', 'tone', 'language',
                    'instructions', 'examples', 'restrictions', 
                    'knowledge_base', 'documents'
                ])
                
                # Exportar cada perfil
                for profile_name, profile in self.profiles["profiles"].items():
                    version = self.get_version(profile_name, profile["active_version"])
                    if not version:
                        continue
                    
                    instructions = '|'.join(version.get('instructions', []))
                    examples = '||'.join(version.get('examples', []))
                    restrictions = '|'.join(version.get('restrictions', []))
                    
                    kb = version.get('knowledge_base', {})
                    kb_str = '|'.join([f"{k}={v['value']}" for k, v in kb.items()])
                    
                    docs = version.get('documents', [])
                    docs_str = '||'.join([f"{doc['name']}::{doc['content']}" for doc in docs])
                    
                    writer.writerow([
                        profile['name'],
                        profile.get('description', ''),
                        profile.get('type', 'general'),
                        version.get('system_prompt', ''),
                        version.get('context', ''),
                        version.get('tone', 'profesional'),
                        version.get('language', 'español'),
                        instructions,
                        examples,
                        restrictions,
                        kb_str,
                        docs_str
                    ])
            
            return True
        except Exception as e:
            print(f"Error exportando todos los perfiles a CSV: {e}")
            return False
    
    # ===== IMPORTACIÓN DE CATÁLOGO DE VEHÍCULOS =====
    
    def import_vehicle_catalog_from_csv(self, csv_path: str, profile_name: str = None) -> Optional[str]:
        """Importar catálogo de vehículos desde CSV con formato de tabla
        
        El CSV debe tener las siguientes columnas:
        id, marca, modelo, version, año, tipo_carroceria, transmision, capacidad_combustible_lt,
        colores, modelo_motor, potencia_hp, cilindrada, neumaticos, puertas, asientos,
        equipamiento_destacado, garantia_años, garantia_km, link_foto
        
        Cada fila representa un vehículo que se agregará a la base de conocimientos
        
        Args:
            csv_path: Ruta del archivo CSV con el catálogo
            profile_name: Nombre opcional para el perfil (si no se especifica, se usa "Catálogo de Vehículos")
        
        Returns:
            Nombre del perfil creado o None si hubo error
        """
        try:
            # Leer CSV
            vehicles = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    vehicles.append(row)
            
            if not vehicles:
                print("No se encontraron vehículos en el CSV")
                return None
            
            # Nombre del perfil
            if not profile_name:
                profile_name = "Catálogo de Vehículos"
            
            # Verificar si ya existe y agregar sufijo
            original_name = profile_name
            counter = 1
            while profile_name in self.profiles["profiles"]:
                profile_name = f"{original_name} {counter}"
                counter += 1
            
            # Crear perfil base
            description = f"Catálogo de vehículos con {len(vehicles)} modelos importados desde CSV"
            profile = self.create_profile(profile_name, description, "ventas")
            
            # System prompt especializado para vehículos
            system_prompt = """Eres un experto asesor de ventas de vehículos. Tienes conocimiento completo del catálogo de vehículos disponibles y puedes ayudar a los clientes a encontrar el vehículo perfecto según sus necesidades, presupuesto y preferencias.

Cuando un cliente pregunte sobre vehículos:
1. Identifica sus necesidades (tamaño, uso, presupuesto, preferencias)
2. Recomienda modelos específicos del catálogo
3. Destaca características relevantes (motor, equipamiento, colores disponibles)
4. Proporciona detalles técnicos cuando se soliciten
5. Ayuda a comparar diferentes modelos
6. Facilita el proceso de decisión con información clara y precisa"""
            
            # Contexto general
            context = f"""Este perfil contiene información detallada sobre {len(vehicles)} vehículos en nuestro catálogo. 
Cada vehículo incluye especificaciones técnicas completas, equipamiento, colores disponibles y más.

El catálogo se actualiza regularmente y toda la información ha sido importada y verificada."""
            
            # Instrucciones específicas
            instructions = [
                "Saluda cordialmente y pregunta qué tipo de vehículo está buscando el cliente",
                "Identifica necesidades clave: uso del vehículo, número de pasajeros, tipo de conducción",
                "Recomienda vehículos específicos del catálogo basándote en las necesidades",
                "Proporciona detalles técnicos precisos del catálogo cuando se soliciten",
                "Destaca el equipamiento y características únicas de cada modelo",
                "Menciona los colores disponibles cuando sea relevante",
                "Ofrece comparaciones entre modelos cuando el cliente esté indeciso",
                "Proporciona información sobre motores, potencia y consumo",
                "Si tienes foto disponible, ofrece mostrarla al cliente",
                "Mantén un tono profesional pero amigable y consultivo"
            ]
            
            # Actualizar perfil con configuración base
            self.update_version_content(
                profile_name, 
                1,
                system_prompt=system_prompt,
                context=context,
                instructions=instructions,
                tone="profesional",
                language="español"
            )
            
            # Agregar cada vehículo a la base de conocimientos
            for idx, vehicle in enumerate(vehicles):
                vehicle_id = vehicle.get('id', f'VEH_{idx+1}')
                marca = vehicle.get('marca', 'N/A')
                modelo = vehicle.get('modelo', 'N/A')
                version = vehicle.get('version', 'N/A')
                año = vehicle.get('año', 'N/A')
                
                # Crear clave única para el vehículo
                kb_key = f"{marca}_{modelo}_{version}_{año}_{vehicle_id}".replace(' ', '_')
                
                # Construir descripción completa del vehículo
                vehicle_info = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚗 {marca} {modelo} {version} ({año})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 INFORMACIÓN GENERAL:
• ID: {vehicle.get('id', 'N/A')}
• Marca: {marca}
• Modelo: {modelo}
• Versión: {version}
• Año: {año}
• Tipo de Carrocería: {vehicle.get('tipo_carroceria', 'N/A')}

🔧 ESPECIFICACIONES TÉCNICAS:
• Motor: {vehicle.get('modelo_motor', 'N/A')}
• Potencia: {vehicle.get('potencia_hp', 'N/A')} HP
• Cilindrada: {vehicle.get('cilindrada', 'N/A')}
• Transmisión: {vehicle.get('transmision', 'N/A')}
• Capacidad de Combustible: {vehicle.get('capacidad_combustible_lt', 'N/A')} litros

🚙 CARACTERÍSTICAS:
• Puertas: {vehicle.get('puertas', 'N/A')}
• Asientos: {vehicle.get('asientos', 'N/A')}
• Neumáticos: {vehicle.get('neumaticos', 'N/A')}

🎨 COLORES DISPONIBLES:
{vehicle.get('colores', 'N/A')}

⭐ EQUIPAMIENTO DESTACADO:
{vehicle.get('equipamiento_destacado', 'N/A')}

🛡️ GARANTÍA:
• Años: {vehicle.get('garantia_años', 'N/A')} año(s)
• Kilómetros: {vehicle.get('garantia_km', 'N/A')} km

📸 IMAGEN:
{vehicle.get('link_foto', 'No disponible')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
                
                # Agregar a la base de conocimientos
                self.add_to_knowledge_base(profile_name, 1, kb_key, vehicle_info.strip())
            
            # Crear documento resumen del catálogo
            summary_lines = [
                "═" * 60,
                f"📊 RESUMEN DEL CATÁLOGO - {len(vehicles)} VEHÍCULOS",
                "═" * 60,
                ""
            ]
            
            # Agrupar por marca
            vehicles_by_brand = {}
            for vehicle in vehicles:
                marca = vehicle.get('marca', 'Sin marca')
                if marca not in vehicles_by_brand:
                    vehicles_by_brand[marca] = []
                vehicles_by_brand[marca].append(vehicle)
            
            for marca, brand_vehicles in sorted(vehicles_by_brand.items()):
                summary_lines.append(f"\n🏷️ {marca.upper()} ({len(brand_vehicles)} modelos):")
                for v in brand_vehicles:
                    modelo = v.get('modelo', 'N/A')
                    año = v.get('año', 'N/A')
                    version = v.get('version', '')
                    summary_lines.append(f"  • {modelo} {año} {version}".strip())
            
            summary_lines.append("\n" + "═" * 60)
            summary_content = "\n".join(summary_lines)
            
            self.add_document(
                profile_name, 
                1, 
                "Resumen del Catálogo",
                summary_content,
                "catálogo"
            )
            
            # Crear documento con índice de búsqueda rápida
            index_lines = [
                "═" * 60,
                "🔍 ÍNDICE DE BÚSQUEDA RÁPIDA",
                "═" * 60,
                "",
                "Busca vehículos por características:",
                ""
            ]
            
            # Índice por tipo de carrocería
            by_body = {}
            for v in vehicles:
                body_type = v.get('tipo_carroceria', 'Otro')
                if body_type not in by_body:
                    by_body[body_type] = []
                by_body[body_type].append(f"{v.get('marca')} {v.get('modelo')} {v.get('año')}")
            
            index_lines.append("\n📦 POR TIPO DE CARROCERÍA:")
            for body_type, models in sorted(by_body.items()):
                index_lines.append(f"\n{body_type}:")
                for model in models:
                    index_lines.append(f"  • {model}")
            
            # Índice por transmisión
            by_trans = {}
            for v in vehicles:
                trans = v.get('transmision', 'N/A')
                if trans not in by_trans:
                    by_trans[trans] = []
                by_trans[trans].append(f"{v.get('marca')} {v.get('modelo')} {v.get('año')}")
            
            index_lines.append("\n\n⚙️ POR TRANSMISIÓN:")
            for trans, models in sorted(by_trans.items()):
                index_lines.append(f"\n{trans}:")
                for model in models:
                    index_lines.append(f"  • {model}")
            
            index_lines.append("\n" + "═" * 60)
            index_content = "\n".join(index_lines)
            
            self.add_document(
                profile_name,
                1,
                "Índice de Búsqueda",
                index_content,
                "índice"
            )
            
            # Agregar ejemplos de conversación
            examples = [
                f"Cliente: ¿Qué vehículos tienen disponibles?\nBot: ¡Excelente! Tenemos {len(vehicles)} modelos en nuestro catálogo de {', '.join(set(v.get('marca', '') for v in vehicles))}. ¿Qué tipo de vehículo estás buscando? ¿Sedan, SUV, pickup?",
                f"Cliente: Busco un SUV familiar.\nBot: Perfecto, tenemos excelentes opciones de SUV. ¿Cuántos pasajeros necesitas transportar regularmente y cuál es tu presupuesto aproximado?",
                "Cliente: ¿Este modelo viene en color rojo?\nBot: Déjame verificar los colores disponibles para ese modelo específicamente. [Consulta la información de colores del vehículo en la base de conocimientos]"
            ]
            
            self.update_version_content(
                profile_name,
                1,
                examples=examples
            )
            
            # Agregar restricciones
            restrictions = [
                "No inventar especificaciones o características que no estén en el catálogo",
                "Siempre verificar la información en la base de conocimientos antes de responder",
                "No prometer disponibilidad sin confirmar primero",
                "No proporcionar precios sin autorización",
                "Dirigir al cliente a un vendedor para finalizar la compra"
            ]
            
            self.update_version_content(
                profile_name,
                1,
                restrictions=restrictions
            )
            
            print(f"✅ Catálogo importado exitosamente: {len(vehicles)} vehículos agregados al perfil '{profile_name}'")
            return profile_name
            
        except Exception as e:
            print(f"Error importando catálogo de vehículos: {e}")
            import traceback
            traceback.print_exc()
            return None

