from crud.base import CRUDBase
from models.models import Dialog


class DialogueCRUD(CRUDBase):
    """CRUD модели dialog."""


dialog_crud = DialogueCRUD(Dialog)
