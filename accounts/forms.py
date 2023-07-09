from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()  # こっちで先に変数代入する！


class SignupForm(UserCreationForm):
    class Meta:
        model = User  # model = get_user_model() は NG
        fields = ("username", "email")


# password1, password2というフィールドはUserCreationFormの方で設定されているため、
# fieldsの欄には、Userモデルの中にある、
# blankにはできない値であるusernameとemailをセットする。
