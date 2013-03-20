from django.contrib import admin
from lizard_rainapp.models import Setting
from lizard_rainapp.models import RainappConfig


admin.site.register(Setting)
admin.site.register(RainappConfig)
