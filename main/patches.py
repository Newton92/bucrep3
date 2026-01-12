# main/patches.py
from django_model_changes.changes import ChangesMixin

def patch_changes_mixin():
    """Patch pour django_model_changes pour supporter BigAutoField"""
    original_current_state = ChangesMixin.current_state
    
    def patched_current_state(self):
        """Version patchée de current_state"""
        state = {}
        for field in self._meta.fields:
            try:
                # Vérifier si c'est un champ de relation
                if hasattr(field, 'rel') or hasattr(field, 'remote_field'):
                    state[field.name] = getattr(self, field.attname, None)
                else:
                    state[field.name] = field.value_from_object(self)
            except AttributeError:
                # Pour BigAutoField qui n'a pas 'rel'
                state[field.name] = field.value_from_object(self)
        return state
    
    ChangesMixin.current_state = patched_current_state

# Appliquer le patch au démarrage
patch_changes_mixin()