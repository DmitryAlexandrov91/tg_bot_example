"""Константы админ-части бота."""

ACCEPTED_TEXTS = ('да', 'yes', 'y')

DT_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'

FIELD_LABLES = {
    'name': 'имени',
    'full_address': 'адреса',
    'short_address': 'короткого адресса',
    'contact_information': 'контактной информации',
}
FIELDS_RESTAURANT = {
    'name': 'Введите новое название ресторана:',
    'full_address': 'Введите новый полный адрес:',
    'short_address': 'Введите новый короткий адрес:',
    'contact_information': 'Введите новые контактные данные:',
}
PROMPT_MAP = {
    'first_name': 'Введите новое имя:',
    'last_name': 'Введите новую фамилию:',
    'patronymic': 'Введите новое отчество (или «-»):',
    'role': 'Выберите новую роль:',
    'tg_id': 'Введите новый TG_ID (число):',
    'email': 'Введите новый Email:',
    'phone_number': 'Введите новый номер телефона:',
    'timezone': 'Выберите новый часовой пояс:',
    'additional_info': 'Введите новую доп. информацию или - :',
}
FIELDS_USER = {
    'first_name': 'имени',
    'last_name': 'фамилии',
    'patronymic': 'отчества:',
    'role': 'роли',
    'tg_id': 'телеграм id',
    'email': 'почты',
    'phone_number': 'номера',
    'timezone': 'часового пояса',
    'additional_info': 'доп. информации',
}
FIELDS_ROADMAP_TEMPLATES = {
    'name': 'Введите новое название шаблона дорожной карты:',
    'description': 'Введите новое описание шаблона дорожной карты:',
}
FIELDS_RT_PLURAL = {
    'name': 'названия шаблона дорожной карты',
    'description': 'описание шаблона дорожной карты',
}
