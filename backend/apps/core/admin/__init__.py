from django.contrib import admin
from .log_admin import *
from .sync_admin import *
from .technician_admin import *
from .tenant_admin import *
from .user_admin import *

admin.site.site_header = "SolidField Admin Panel"
