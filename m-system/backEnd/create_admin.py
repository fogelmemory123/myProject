from extensions import db
from models import User, Role, Branch
from app import app  # ודא שהנתיב נכון לאפליקציה הראשית שלך

with app.app_context():
    # יצירת רולים אם לא קיימים
    roles = ['אדמין', 'מנהל סניף', 'מקבל שירות']
    for role_name in roles:
        existing_role = Role.query.filter_by(name=role_name).first()
        if not existing_role:
            new_role = Role(name=role_name)
            db.session.add(new_role)
            print(f"🔑 נוצר רול: {role_name}")
    db.session.commit()

    # יצירת סניפים אם לא קיימים
    branches = ['תל אביב', 'ירושלים', 'קיסריה', 'יוקנעם', 'באר שבע']
    for city_name in branches:
        existing_branch = Branch.query.filter_by(city=city_name).first()
        if not existing_branch:
            new_branch = Branch(city=city_name)
            db.session.add(new_branch)
            print(f"📍 נוצר סניף: {city_name}")
    db.session.commit()

    # שליפת רול "אדמין"
    role = Role.query.filter_by(name='אדמין').first()
    if not role:
        print("❌ רול 'אדמין' לא נמצא במסד הנתונים.")
        exit()

    # שליפת סניף תל אביב
    branch = Branch.query.filter_by(city="תל אביב").first()
    if not branch:
        print("❌ סניף 'תל אביב' לא נמצא במסד הנתונים.")
        exit()

    # בדיקת קיום לפי אימייל
    email = 'fogelmemory@gmail.com'
    if User.query.filter_by(email=email).first():
        print("⚠️ משתמש עם האימייל הזה כבר קיים.")
    else:
        user = User(
            first_name="דניאל",
            last_name="פוגל",
            email=email,
            birth_date="1990-01-01",
            branch_id=branch.id,
            role_id=role.id
        )
        user.set_password("1234")
        db.session.add(user)
        db.session.commit()
        print("✅ משתמש אדמין נוצר בהצלחה:")
        print(f"שם מלא: {user.first_name} {user.last_name}")
        print(f"אימייל: {user.email}")
        print(f"סניף: {branch.city}")
        print(f"סיסמה: 1234 (הוצפנה)")
# from app import app
# from extensions import db
# from models import Branch

# with app.app_context():
#     branch = Branch.query.filter_by(city="יוקנעם").first()
#     if branch:
#         branch.city = "יקנעם"
#         db.session.commit()
#         print("✅ עודכן: שם הסניף שונה ל-יקנעם")
#     else:
#         print("❌ לא נמצא סניף בשם 'יוקנעם'")

