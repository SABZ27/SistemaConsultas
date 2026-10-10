from email_validator import EmailNotValidError, validate_email


def validar_correo(v):
    if isinstance(v, str) and v.strip():
        try:
            validate_email(v, check_deliverability=False)
        except EmailNotValidError as exc:
            raise ValueError("El correo no tiene un formato válido") from exc
    return v