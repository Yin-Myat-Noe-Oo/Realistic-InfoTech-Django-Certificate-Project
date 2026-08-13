from .models import StoreSettings


def store_settings(request):
    """Make the store settings available to every template."""
    settings, _ = StoreSettings.objects.get_or_create(id=1)
    return {"store_settings": settings}
