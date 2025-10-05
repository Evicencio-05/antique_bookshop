import sys
from django.conf import settings
from django.template import Context, Template
from django.test.utils import setup_test_environment

from book_shop_here.forms import AuthorForm

setup_test_environment()

try:
    tmpl = Template("""{% load crispy_forms_tags %}{{ form|crispy }}""")
    html = tmpl.render(Context({"form": AuthorForm()}))
    print("OK length:", len(html))
except Exception as e:
    import traceback
    traceback.print_exc()
    print("ERROR:", type(e).__name__, str(e))
